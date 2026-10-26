# Reading the experiment

## Three separate facts

1. `node.complete` means the node body reached its return path. It is logged immediately before the result returns.
2. `slow_result_saved` means the failed run's checkpoint pending writes include B's channel, `b`.
3. `slow_total_calls` comes from a separate SQLite counter after a fresh process resumes the graph.

The final state can be correct even when B ran twice. A state-equality test alone cannot detect this bug.

## Independent axes

`mode=sync` selects `invoke`; `mode=async` selects `ainvoke`. Separately, `durability=sync`, `async` or `exit` controls when state is persisted. Async execution does not imply async durability.

With async execution, `finish` deliberately lets B finish despite cancellation. `cancel` lets B raise `CancelledError`. A cancelled B has no completed result, so retrying it is expected.

## Two processes

The fail process runs until the injected error and reads the checkpoint. It exits. The resume process rebuilds the graph against the same SQLite database and invokes it with `None`. Their PIDs are checked to differ.

`activity.sqlite3` counts starts and completed bodies; `checkpoints.sqlite3` stores graph state. Both contain only synthetic data. Each run uses fresh files.

The parent invokes the same worker file with explicit interpreters. Its import path starts in the lab package directory, rather than the controller's site-packages, so each interpreter loads its own LangGraph.

## Timing

The delay creates a late sibling. Scheduling can change on a heavily loaded machine. A missing baseline reproduction is reported explicitly. Changing `--delay-ms` changes fault scheduling, not model performance.

HTML replay advances by recorded event at presentation speed. Each event shows measured per-process elapsed time. There is no shared monotonic clock across independent processes.

## Source identity

`provenance.json` declares expected revisions and hashes. Reports separately record actual versions and source fingerprints. `source_verification` indicates whether they match. Custom interpreters can differ from the pinned pair; such observations should not be described as validating that pair.

A runtime change across stages or repetitions makes the comparison inconclusive. Identical source hashes on both sides cannot establish a fix.

## Exit codes

| Command | Code | Meaning |
|---|---:|---|
| `compare` | 0 | Candidate checks pass and a baseline lost-write case was observed |
| `compare` | 2 | Inconclusive result, candidate failure, timeout or command/setup error |
| `run` | 0 | Recovery checks passed for that implementation |
| `run` | 1 | The experiment ran but recovery checks failed |
| `run` | 2 | Timeout or command/setup error |

An expected baseline failure is evidence for `compare`; it is not hidden.
