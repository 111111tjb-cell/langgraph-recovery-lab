# Recovery experiment

Baseline lost completed work; candidate preserved it.

Generated: 2026-10-25T14:24:04.686749+00:00 (UTC).

These are measured local observations of a synthetic failure, not a throughput benchmark or an exactly-once guarantee.

| Environment | Case | Execution | Durability | Async policy | B completed before exit | B saved | B total calls | Observation |
|---|---:|---|---|---|---|---|---:|---|
| baseline | 1 | sync | exit | - | True | False | 2 | completed-result-lost |
| baseline | 2 | sync | sync | - | True | True | 1 | completed-result-preserved |
| baseline | 3 | sync | async | - | True | True | 1 | completed-result-preserved |
| baseline | 4 | async | exit | finish | True | False | 2 | completed-result-lost |
| baseline | 5 | async | sync | finish | True | True | 1 | completed-result-preserved |
| baseline | 6 | async | async | finish | True | True | 1 | completed-result-preserved |
| baseline | 7 | async | exit | cancel | False | False | 2 | unfinished-node-retried |
| baseline | 8 | async | sync | cancel | False | False | 2 | unfinished-node-retried |
| baseline | 9 | async | async | cancel | False | False | 2 | unfinished-node-retried |
| baseline | 10 | sync | exit | - | True | False | 2 | completed-result-lost |
| baseline | 11 | sync | sync | - | True | True | 1 | completed-result-preserved |
| baseline | 12 | sync | async | - | True | True | 1 | completed-result-preserved |
| baseline | 13 | async | exit | finish | True | False | 2 | completed-result-lost |
| baseline | 14 | async | sync | finish | True | True | 1 | completed-result-preserved |
| baseline | 15 | async | async | finish | True | True | 1 | completed-result-preserved |
| baseline | 16 | async | exit | cancel | False | False | 2 | unfinished-node-retried |
| baseline | 17 | async | sync | cancel | False | False | 2 | unfinished-node-retried |
| baseline | 18 | async | async | cancel | False | False | 2 | unfinished-node-retried |
| baseline | 19 | sync | exit | - | True | False | 2 | completed-result-lost |
| baseline | 20 | sync | sync | - | True | True | 1 | completed-result-preserved |
| baseline | 21 | sync | async | - | True | True | 1 | completed-result-preserved |
| baseline | 22 | async | exit | finish | True | False | 2 | completed-result-lost |
| baseline | 23 | async | sync | finish | True | True | 1 | completed-result-preserved |
| baseline | 24 | async | async | finish | True | True | 1 | completed-result-preserved |
| baseline | 25 | async | exit | cancel | False | False | 2 | unfinished-node-retried |
| baseline | 26 | async | sync | cancel | False | False | 2 | unfinished-node-retried |
| baseline | 27 | async | async | cancel | False | False | 2 | unfinished-node-retried |
| candidate | 1 | sync | exit | - | True | True | 1 | completed-result-preserved |
| candidate | 2 | sync | sync | - | True | True | 1 | completed-result-preserved |
| candidate | 3 | sync | async | - | True | True | 1 | completed-result-preserved |
| candidate | 4 | async | exit | finish | True | True | 1 | completed-result-preserved |
| candidate | 5 | async | sync | finish | True | True | 1 | completed-result-preserved |
| candidate | 6 | async | async | finish | True | True | 1 | completed-result-preserved |
| candidate | 7 | async | exit | cancel | False | False | 2 | unfinished-node-retried |
| candidate | 8 | async | sync | cancel | False | False | 2 | unfinished-node-retried |
| candidate | 9 | async | async | cancel | False | False | 2 | unfinished-node-retried |
| candidate | 10 | sync | exit | - | True | True | 1 | completed-result-preserved |
| candidate | 11 | sync | sync | - | True | True | 1 | completed-result-preserved |
| candidate | 12 | sync | async | - | True | True | 1 | completed-result-preserved |
| candidate | 13 | async | exit | finish | True | True | 1 | completed-result-preserved |
| candidate | 14 | async | sync | finish | True | True | 1 | completed-result-preserved |
| candidate | 15 | async | async | finish | True | True | 1 | completed-result-preserved |
| candidate | 16 | async | exit | cancel | False | False | 2 | unfinished-node-retried |
| candidate | 17 | async | sync | cancel | False | False | 2 | unfinished-node-retried |
| candidate | 18 | async | async | cancel | False | False | 2 | unfinished-node-retried |
| candidate | 19 | sync | exit | - | True | True | 1 | completed-result-preserved |
| candidate | 20 | sync | sync | - | True | True | 1 | completed-result-preserved |
| candidate | 21 | sync | async | - | True | True | 1 | completed-result-preserved |
| candidate | 22 | async | exit | finish | True | True | 1 | completed-result-preserved |
| candidate | 23 | async | sync | finish | True | True | 1 | completed-result-preserved |
| candidate | 24 | async | async | finish | True | True | 1 | completed-result-preserved |
| candidate | 25 | async | exit | cancel | False | False | 2 | unfinished-node-retried |
| candidate | 26 | async | sync | cancel | False | False | 2 | unfinished-node-retried |
| candidate | 27 | async | async | cancel | False | False | 2 | unfinished-node-retried |

## Loaded runtimes

Expected source references are checked against loaded source fingerprints:

```json
{
  "baseline": {
    "matches_expected_source": true,
    "expected_ref": "4c52e129eb1ab69a3da58b799f67929f77d81149"
  },
  "candidate": {
    "matches_expected_source": true,
    "expected_ref": "e3263b3742852d4e1576baa60d9307aa0e03f8df"
  }
}
```

### baseline

Python 3.12.4, Windows

```json
{
  "python": "3.12.4",
  "platform": "Windows",
  "packages": {
    "langgraph": "1.2.17",
    "langgraph-checkpoint": "4.3.0",
    "langgraph-checkpoint-sqlite": "3.1.2",
    "langchain-core": "1.6.5",
    "aiosqlite": "0.22.1"
  },
  "source_sha256_lf": {
    "langgraph.pregel._runner": "dc835c835cbd2c783ff1df3ca46343ecab9b4a7f534ed0083be8d0664d21816e",
    "langgraph.pregel.main": "c96d4424e7a75388aef09afeaa8fcfe17c026e60dafca1331003775ca1bf0ffc"
  }
}
```

### candidate

Python 3.12.4, Windows

```json
{
  "python": "3.12.4",
  "platform": "Windows",
  "packages": {
    "langgraph": "1.2.17",
    "langgraph-checkpoint": "4.3.0",
    "langgraph-checkpoint-sqlite": "3.1.2",
    "langchain-core": "1.6.5",
    "aiosqlite": "0.22.1"
  },
  "source_sha256_lf": {
    "langgraph.pregel._runner": "23b0eb49a9bb31735e6642635e26460502b0b14338414c5b2d5b11c1ec3509c6",
    "langgraph.pregel.main": "5391eedd8be2df27a9f7854b656e76c6e7f00719e5ee2d7ad2a98fea0f45463e"
  }
}
```

## Interpretation

- A is `flaky`: it intentionally fails once and should have two total calls after recovery.
- B is `slow`: if it completed during the failed attempt, its saved result should prevent a second call.
- An async B that honors cancellation has no completed result to preserve; retrying it is expected.
- The fail and resume stages use independent Python processes with the same SQLite files.
- Inspect `comparison.json`, per-stage stderr and trace files for the underlying observations.
- A missing reproduction is reported explicitly; it is not evidence of an improvement.
