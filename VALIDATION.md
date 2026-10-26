# Validation on 2026-10-25

Windows, Python 3.12.4.

- 21 unit and fresh-process integration tests passed, with no skips.
- Matrix: 27 baseline and 27 candidate cases across execution, durability and cancellation policies, repeated three times.
- Baseline: 6 completed-result-loss observations in exit mode. Candidate: all 27 recovery checks passed.
- 108 independent worker processes in the matrix. Source fingerprints matched both pinned revisions.
- 41 runtime package version constraints matched in both environments.
- Ruff formatting/lint passed. Wheel built and installed in a fresh controller environment; the CLI ran successfully outside the source tree.
- The default report was visually checked in the browser; replay showed 28 recorded events with no console errors.

The initial sandbox async run timed out before entering any nodes. A minimal asyncio program also blocked in Windows socketpair, while the same program passed in the normal host environment. The successful async matrix and integration tests used that normal environment. This environment failure is not counted as a LangGraph behavior observation.

Linux/macOS and hosted CI are not claimed as tested. This is a controlled recovery experiment, not a throughput benchmark, hard-kill recovery test or exactly-once guarantee. The original fork's 52 regression cases are separate from these lab checks.

See [machine-readable record](VALIDATION_RESULTS.json), [default evidence](docs/results/default/comparison.md) and [full matrix](docs/results/matrix/comparison.md).
