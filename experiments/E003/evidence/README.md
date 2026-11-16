# E003 evidence

Evaluator-only artifacts. Never copy these harnesses or the oracle path into an agent workspace.
`probe.py` and `diagnose.py` retain the exact local paths used; they require the preserved run and its external `launch-env.json`. The latter is intentionally excluded because it contains host environment values. These are diagnostic artifacts, not a supported sandbox implementation.

- round 0: uv aborted at SystemConfiguration; no tool/LLM completion.
- correction 1: added only configd mach lookup. uv and OpenCode debug config succeeded. openpyxl failed at the system MIME table; stdlib path tests denied sibling/oracle/symlink and parent listing; local HTTP returned connection refused.
- correction 2: added exact public MIME file plus numeric IPv4 remote rule; Apple profile parser rejected the numeric host, exit 65. No process started under that profile.

No further policy correction or agent E2E was attempted. Empty stdout/stderr files are intentionally retained where recorded.
