"""Return one boolean for Graph auth inside the future worker boundary."""

from __future__ import annotations

import contextlib
import io
import json

from src.graph.readiness import graph_auth_ready


def main() -> int:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
        io.StringIO()
    ):
        ready = graph_auth_ready()
    print(json.dumps({"worker_graph_auth_ready": ready}, separators=(",", ":")))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
