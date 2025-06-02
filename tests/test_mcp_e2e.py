import json, pytest
from .client_runner import call_client

@pytest.mark.asyncio
async def test_list_tools(ctx):
    out = await call_client(ctx["client"], ["list_tools"], ctx["extra_env"])
    assert "code_exec_python" in out

@pytest.mark.asyncio
async def test_code_exec(ctx):
    payload = json.dumps(
        {"name": "code_exec_python", "arguments": {"code": "print(2+2)"}}
    )
    out = await call_client(
        ctx["client"],
        ["call_tool", "--args", payload],
        ctx["extra_env"],
    )
    assert '"4"' in out or "'4'" in out
