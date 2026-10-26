# Validation

## Local run on 2026-10-25

Windows, Python 3.12.4.

- 21 unit and fresh-process integration tests passed, with no skips.
- Matrix: 27 baseline and 27 candidate cases across execution, durability and cancellation policies, repeated three times.
- Baseline: 6 completed-result-loss observations in exit mode. Candidate: all 27 recovery checks passed.
- 108 independent worker processes in the matrix. Source fingerprints matched both pinned revisions.
- 41 runtime package version constraints matched in both environments.
- Ruff formatting/lint passed. Wheel built and installed in a fresh controller environment; the CLI ran successfully outside the source tree.
- The default report was visually checked in the browser; replay showed 28 recorded events with no console errors.

The initial sandbox async run timed out before entering any nodes. A minimal asyncio program also blocked in Windows socketpair, while the same program passed in the normal host environment. The successful async matrix and integration tests used that normal environment. This environment failure is not counted as a LangGraph behavior observation.

This is a controlled recovery experiment, not a throughput benchmark, hard-kill recovery test or exactly-once guarantee. The original fork's 52 regression cases are separate from these lab checks.

## Hosted CI on 2026-10-26

[GitHub Actions run 40259639626](https://github.com/111111tjb-cell/langgraph-recovery-lab/actions/runs/40259639626) completed successfully at source commit `179aa63e10507a8c46d0abe688dded444e273f88`.

| Check | Ubuntu | Windows | macOS |
| --- | --- | --- | --- |
| Ruff lint and formatting | Passed | Passed | Passed |
| Standard-library unit suite | Passed | Passed | Passed |
| Unit and fresh-process integration suite, 21 tests | Passed | Passed | Not run |
| Recovery matrix, 9 baseline + 9 candidate cases | Passed | Passed | Not run |

Each hosted recovery matrix ran once per scenario. On each platform, the baseline lost completed results in 2 exit-mode cases; the candidate preserved all 6 completed-result cases. Both environments retried the 3 intentionally unfinished cancellation cases. These 18 cases per platform are separate from the local 54-case matrix above.

The run uploaded `recovery-ubuntu-latest` and `recovery-windows-latest` report artifacts. GitHub artifact retention applies; the checked-in local evidence remains available in this repository. macOS graph execution has not been validated.

See [machine-readable record](VALIDATION_RESULTS.json), [default evidence](docs/results/default/comparison.md) and [full matrix](docs/results/matrix/comparison.md).
