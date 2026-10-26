"""The controlled failure runs unchanged in both environments."""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TypedDict


@dataclass(frozen=True)
class Options:
    mode: str = "sync"
    durability: str = "exit"
    async_policy: str = "finish"
    delay_ms: int = 200

    def __post_init__(self) -> None:
        if self.mode not in {"sync", "async"}:
            raise ValueError("mode must be sync or async")
        if self.durability not in {"exit", "sync", "async"}:
            raise ValueError("durability must be exit, sync or async")
        if self.async_policy not in {"finish", "cancel"}:
            raise ValueError("async_policy must be finish or cancel")
        if not 1 <= self.delay_ms <= 5000:
            raise ValueError("delay_ms must be between 1 and 5000")


class State(TypedDict, total=False):
    a: int
    b: int


class ExpectedFailure(RuntimeError):
    pass


class Activity:
    def __init__(self, directory: Path, stage: str) -> None:
        self.database = directory / "activity.sqlite3"
        if stage == "fail" and self.database.exists():
            raise ValueError("The first stage needs a fresh run directory")
        self.trace_path = directory / f"{stage}.trace.jsonl"
        self.stage = stage
        self.started = time.monotonic()
        self.lock = threading.Lock()
        with sqlite3.connect(self.database) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS activity "
                "(kind TEXT, node TEXT, count INTEGER, PRIMARY KEY(kind, node))"
            )

    def trace(self, event: str, **details: object) -> None:
        item = {
            "stage": self.stage,
            "pid": os.getpid(),
            "elapsed_ms": round((time.monotonic() - self.started) * 1000, 3),
            "event": event,
            **details,
        }
        with self.lock, self.trace_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(item, ensure_ascii=True) + "\n")

    def record(self, kind: str, node: str) -> int:
        with sqlite3.connect(self.database, timeout=10) as connection:
            connection.execute(
                "INSERT INTO activity VALUES (?, ?, 1) "
                "ON CONFLICT(kind, node) DO UPDATE SET count=count+1",
                (kind, node),
            )
            count = connection.execute(
                "SELECT count FROM activity WHERE kind=? AND node=?", (kind, node)
            ).fetchone()[0]
        self.trace(f"node.{kind}", node=node, count=count)
        return count

    def totals(self, kind: str) -> dict[str, int]:
        with sqlite3.connect(self.database) as connection:
            return dict(
                connection.execute(
                    "SELECT node, count FROM activity WHERE kind=? ORDER BY node",
                    (kind,),
                )
            )


def runtime_info() -> dict:
    fingerprints = {}
    for module_name in ("langgraph.pregel._runner", "langgraph.pregel.main"):
        module = importlib.import_module(module_name)
        source = Path(module.__file__).read_bytes().replace(b"\r\n", b"\n")
        fingerprints[module_name] = hashlib.sha256(source).hexdigest()
    return {
        "python": platform.python_version(),
        "platform": platform.system(),
        "packages": {
            name: importlib.metadata.version(name)
            for name in (
                "langgraph",
                "langgraph-checkpoint",
                "langgraph-checkpoint-sqlite",
                "langchain-core",
                "aiosqlite",
            )
        },
        "source_sha256_lf": fingerprints,
    }


def run_stage(directory: Path, stage: str, options: Options) -> dict:
    if stage not in {"fail", "resume"}:
        raise ValueError("Unknown stage")
    directory.mkdir(parents=True, exist_ok=True)
    if stage == "resume" and not (directory / "checkpoints.sqlite3").is_file():
        raise ValueError("No checkpoint database to resume")
    activity = Activity(directory, stage)
    activity.trace("process.start", options=asdict(options))
    result = (
        _run_sync(directory, stage, options, activity)
        if options.mode == "sync"
        else asyncio.run(_run_async(directory, stage, options, activity))
    )
    activity.trace("process.complete")
    return {
        "stage": stage,
        "pid": os.getpid(),
        **result,
        "calls": activity.totals("start"),
        "completed": activity.totals("complete"),
        "runtime": runtime_info(),
    }


def _builder(flaky, slow):
    from langgraph.graph import END, START, StateGraph

    builder = StateGraph(State)
    builder.add_node("flaky", flaky)
    builder.add_node("slow", slow)
    builder.add_edge(START, "flaky")
    builder.add_edge(START, "slow")
    builder.add_edge(["flaky", "slow"], END)
    return builder


def _run_sync(
    directory: Path, stage: str, options: Options, activity: Activity
) -> dict:
    from langgraph.checkpoint.sqlite import SqliteSaver

    started = threading.Event()

    def flaky(state: State) -> dict:
        if activity.record("start", "flaky") == 1:
            if not started.wait(10):
                raise TimeoutError("The sibling did not start")
            activity.trace("failure.injected", node="flaky")
            raise ExpectedFailure("intentional first-attempt failure")
        activity.record("complete", "flaky")
        return {"a": 1}

    def slow(state: State) -> dict:
        activity.record("start", "slow")
        started.set()
        time.sleep(options.delay_ms / 1000)
        activity.record("complete", "slow")
        return {"b": 1}

    config = {"configurable": {"thread_id": "recovery-lab"}}
    with SqliteSaver.from_conn_string(str(directory / "checkpoints.sqlite3")) as saver:
        graph = _builder(flaky, slow).compile(checkpointer=saver)
        if stage == "fail":
            try:
                graph.invoke({}, config, durability=options.durability)
            except ExpectedFailure:
                activity.trace("graph.expected_failure")
            else:
                raise AssertionError("The injected failure did not propagate")
            checkpoint = saver.get_tuple(config)
            if checkpoint is None:
                raise AssertionError("No exit checkpoint was saved")
            saved = sorted({key for _, key, _ in checkpoint.pending_writes})
            activity.trace("checkpoint.snapshot", saved_channels=saved)
            return {"saved_channels": saved}
        state = graph.invoke(None, config, durability=options.durability)
        activity.trace("graph.resumed", state=state)
        return {"state": state}


async def _run_async(
    directory: Path, stage: str, options: Options, activity: Activity
) -> dict:
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    started = asyncio.Event()

    async def flaky(state: State) -> dict:
        if activity.record("start", "flaky") == 1:
            await asyncio.wait_for(started.wait(), timeout=10)
            activity.trace("failure.injected", node="flaky")
            raise ExpectedFailure("intentional first-attempt failure")
        activity.record("complete", "flaky")
        return {"a": 1}

    async def slow(state: State) -> dict:
        activity.record("start", "slow")
        started.set()
        while True:
            try:
                await asyncio.sleep(options.delay_ms / 1000)
                break
            except asyncio.CancelledError:
                activity.trace("node.cancel_requested", node="slow")
                if options.async_policy == "cancel":
                    activity.trace("node.cancelled", node="slow")
                    raise
                # Simulate work that finishes despite a cancellation request.
        activity.record("complete", "slow")
        return {"b": 1}

    config = {"configurable": {"thread_id": "recovery-lab"}}
    async with AsyncSqliteSaver.from_conn_string(
        str(directory / "checkpoints.sqlite3")
    ) as saver:
        graph = _builder(flaky, slow).compile(checkpointer=saver)
        if stage == "fail":
            try:
                await graph.ainvoke({}, config, durability=options.durability)
            except ExpectedFailure:
                activity.trace("graph.expected_failure")
            else:
                raise AssertionError("The injected failure did not propagate")
            checkpoint = await saver.aget_tuple(config)
            if checkpoint is None:
                raise AssertionError("No exit checkpoint was saved")
            saved = sorted({key for _, key, _ in checkpoint.pending_writes})
            activity.trace("checkpoint.snapshot", saved_channels=saved)
            return {"saved_channels": saved}
        state = await graph.ainvoke(None, config, durability=options.durability)
        activity.trace("graph.resumed", state=state)
        return {"state": state}
