import asyncio, os, subprocess, shlex, pytest
from pathlib import Path

ROOT        = Path(__file__).resolve().parents[1]
API_KEY     = os.getenv("API_KEY", "local-test-key")
WAIT_SECS   = 15         # generous for CI

# ------------------------------------------------------------------ helpers
async def _wait_port(port: int, proc: subprocess.Popen[str], timeout: int = WAIT_SECS):
    """
    Poll a TCP port until it opens.
    If the server dies first, dump its stdout/stderr so you can read the traceback.
    """
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        try:
            reader, _ = await asyncio.open_connection("127.0.0.1", port)
            reader.close()
            return
        except Exception:
            await asyncio.sleep(0.25)

    # Timed-out: capture whatever the server printed and raise
    proc.terminate()
    _ = proc.wait()
    output = proc.stdout.read() if proc.stdout else ""
    raise RuntimeError(
        f"Timed out waiting for 127.0.0.1:{port}\n\n--- server output ---\n{output}"
    )

def _start_uvicorn(import_path: str, port: int) -> subprocess.Popen[str]:
    env = os.environ | {"API_KEY": API_KEY, "PYTHONPATH": str(ROOT)}
    return subprocess.Popen(
        shlex.split(f"uvicorn {import_path} --port {port} --no-access-log"),
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

# ------------------------------------------------------------------ contexts
async def ctx_http_local():
    proc = _start_uvicorn("src.streamable_http_server:app", 8001)
    try:
        await _wait_port(8001, proc)
        yield {
            "client":    "streamable_http_client",
            "extra_env": {"API_KEY": API_KEY, "MCP_SERVER_URL": "http://127.0.0.1:8001"},
        }
    finally:
        proc.terminate(); proc.wait()


async def ctx_sse_local():
    proc = _start_uvicorn("src.sse_server:app", 8002)
    try:
        await _wait_port(8002, proc)
        yield {
            "client":    "sse_client",
            "extra_env": {"API_KEY": API_KEY, "MCP_SERVER_URL": "http://127.0.0.1:8002"},
        }
    finally:
        proc.terminate(); proc.wait()


async def ctx_stdio_local():
    yield {"client": "stdio_client", "extra_env": {}}

async def ctx_remote():
    url, key = os.getenv("MCP_SERVER_URL"), os.getenv("API_KEY")
    if not url or not key:
        pytest.skip("remote env vars missing")
    yield {
        "client":    "streamable_http_client",
        "extra_env": {"API_KEY": key, "MCP_SERVER_URL": url.rstrip("/")},
    }

# ------------------------------------------------------------------ fixture
_FIX = {
    "http_local" : ctx_http_local,
    "sse_local"  : ctx_sse_local,
    "stdio_local": ctx_stdio_local,
    "remote"     : ctx_remote,
}

@pytest.fixture(params=_FIX, ids=list(_FIX))
async def ctx(request):
    async for c in _FIX[request.param]():
        yield c
