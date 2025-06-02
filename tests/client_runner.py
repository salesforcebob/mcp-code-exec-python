"""
Launch one of the example_clients in a fresh subprocess and return STDOUT.
This avoids Mando’s global sub-parser registration conflicts.
"""
from __future__ import annotations
import asyncio, os, sys, subprocess, textwrap
from pathlib import Path
from typing import Sequence, Mapping

ROOT      = Path(__file__).resolve().parents[1]
EXAMPLES  = ROOT / "example_clients"
PYTHON_EXE = sys.executable


async def call_client(
    module_name: str,
    cli_args: Sequence[str],
    extra_env: Mapping[str, str] | None = None,
) -> str:
    env = os.environ.copy() | (extra_env or {})

    cmd = [
        PYTHON_EXE,
        "-m",
        f"example_clients.{module_name}",
        "mcp",
        *cli_args,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out_b, err_b = await proc.communicate()
    out = out_b.decode()
    err = err_b.decode()
    if proc.returncode:
        raise RuntimeError(
            textwrap.dedent(
                f"""\
                Client {module_name} exited with {proc.returncode}
                CMD   : {" ".join(cmd)}
                STDERR:
                {err}"""
            )
        )
    return out
