# Contributing

This independent experiment is not the LangGraph project. Discuss LangGraph implementation changes with its upstream maintainers.

Useful contributions include reproductions on another platform, clearer installation instructions and focused additional recovery scenarios. Record actual outcomes, including missing reproductions.

Before sending a change:

```sh
python -m unittest discover -s tests -v
python -m recovery_lab compare --matrix --include-cancelled
```

Run Ruff format/lint checks when Python changes. Set `RECOVERY_LAB_TEST_PYTHON` to the candidate interpreter to enable fresh-process integration tests.

Include runtime versions, source hashes, scenario options and sanitized relevant stderr. Do not share credentials or unrelated application data.

AI assistance is welcome when changes are reviewed and validated. Disclose substantial assistance. Avoid unverified claims about performance, exactly-once behavior, platform coverage or upstream acceptance.
