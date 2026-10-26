"""Build a static public demo directly from the checked-in measured report."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from recovery_lab.report import html_report

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/111111tjb-cell/langgraph-recovery-lab"
PUBLIC_URL = "https://111111tjb-cell.github.io/langgraph-recovery-lab/"


def replace_once(document: str, old: str, new: str) -> str:
    if document.count(old) != 1:
        raise ValueError(f"Report template changed: expected one {old!r}")
    return document.replace(old, new, 1)


def build_demo(report: dict) -> str:
    document = html_report(report)
    recorded_date = html.escape(report["generated_at"].split("T", 1)[0])
    document = replace_once(
        document,
        "<title>LangGraph recovery lab — measured comparison</title>",
        "<title>LangGraph Recovery Lab — interactive recorded demo</title>"
        '<meta name="description" content="Replay a measured LangGraph parallel failure and fresh-process recovery. Compare saved results, node calls and source fingerprints without installing Python.">'
        f'<link rel="canonical" href="{PUBLIC_URL}">'
        '<meta property="og:title" content="LangGraph Recovery Lab">'
        '<meta property="og:description" content="The final state can be correct even when completed work runs twice. Inspect a measured recovery experiment.">'
        f'<meta property="og:url" content="{PUBLIC_URL}">',
    )
    document = replace_once(
        document,
        "</style>",
        ".demo-nav{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:42px}"
        ".demo-brand{font-weight:750;color:#e8eef9;text-decoration:none}"
        ".demo-links{display:flex;align-items:center;gap:18px;flex-wrap:wrap;font-size:14px}"
        ".demo-star{border:1px solid #74d7c2;border-radius:8px;padding:9px 14px;text-decoration:none}"
        ".demo-note{border-left:3px solid #74d7c2;padding:10px 16px;background:#142135}"
        "a:focus-visible,button:focus-visible,select:focus-visible{outline:3px solid #74d7c2;outline-offset:4px}"
        "#reproduce{margin-top:32px}#reproduce code{font-size:14px;line-height:1.8}"
        "@media(max-width:720px){.demo-nav{margin-bottom:30px}.demo-links{gap:14px}.demo-star{padding:8px 10px}}"
        "</style>",
    )
    document = replace_once(
        document,
        "<header>",
        '<nav class="demo-nav" aria-label="Project navigation">'
        f'<a class="demo-brand" href="{REPOSITORY}">LangGraph Recovery Lab</a>'
        '<div class="demo-links">'
        '<a href="results/matrix/">Full recorded matrix</a>'
        '<a href="#reproduce">Run it yourself</a>'
        f'<a lang="zh-CN" href="{REPOSITORY}/blob/main/docs/README.zh-CN.md">中文说明</a>'
        f'<a class="demo-star" href="{REPOSITORY}">☆ Star on GitHub</a>'
        "</div></nav><header>",
    )
    document = replace_once(
        document,
        "LANGGRAPH RECOVERY LAB / LOCAL OBSERVATIONS",
        f"INTERACTIVE RECORDED DEMO / {recorded_date}",
    )
    document = replace_once(
        document,
        '</header><div class="verdict" id="verdict"></div>',
        '<p class="muted demo-note">Explore actual saved events without installing Python. '
        "The replay does not execute LangGraph in your browser. "
        "The candidate is an experimental fork, not an official LangGraph release.</p>"
        '</header><div class="verdict" id="verdict"></div>',
    )
    document = replace_once(
        document,
        "<details><summary>Exact runtime versions and source fingerprints</summary>",
        '<section id="reproduce" aria-labelledby="reproduce-title">'
        '<h2 id="reproduce-title">Reproduce it on your machine</h2>'
        '<p class="muted">Use Python 3.12+. Preparation downloads pinned dependencies; '
        "the experiment uses local SQLite with no LLM, API key or external database.</p>"
        f"<pre><code>git clone {REPOSITORY}.git\n"
        "cd langgraph-recovery-lab\n"
        "python -m recovery_lab prepare\n"
        "python -m recovery_lab compare</code></pre>"
        '<p class="muted">Completed work should be reused. Work cancelled before producing a result should be retried. '
        f'<a href="{REPOSITORY}/blob/main/VALIDATION.md">See the verified platform scope and limits</a>.</p>'
        "</section><details><summary>Exact runtime versions and source fingerprints</summary>",
    )
    document = replace_once(
        document, 'href="comparison.json"', 'href="results/default/comparison.json"'
    )
    return replace_once(
        document, 'href="comparison.md"', 'href="results/default/comparison.md"'
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Fail if the published demo is stale"
    )
    args = parser.parse_args()
    report = json.loads(
        (ROOT / "docs/results/default/comparison.json").read_text(encoding="utf-8")
    )
    output = ROOT / "docs/index.html"
    expected = build_demo(report)
    if args.check:
        if not output.exists() or output.read_text(encoding="utf-8") != expected:
            parser.exit(1, "Demo is stale. Run: python -m scripts.build_demo\n")
        print("Published demo matches the measured report.")
    else:
        output.write_text(expected, encoding="utf-8", newline="\n")
        print(f"Built {output.relative_to(ROOT)} from the measured default report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
