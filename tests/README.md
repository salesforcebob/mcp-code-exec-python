# 🧪 End-to-End Test Suite (`tests/`)

This folder contains a pytest harness that validates every MCP transport your repo supports.

| Context ID   | What’s exercised                                    |
|--------------|-----------------------------------------------------|
| `http_local` | Streamable HTTP on `localhost:8000/mcp/`            |
| `sse_local`  | SSE on `localhost:8000/mcp/sse`                     |
| `stdio_local`| STDIO (example client boots its own server)         |
| `remote`     | • **STDIO** via a one-off dyno<br>• The transport named in **`$REMOTE_SERVER_TYPE`** (`streamable_http_server` or `sse_server`) running on your Heroku app |

If the remote dyno is asleep or scaled to 0, the two remote `$REMOTE_SERVER_TYPE` tests are **auto-skipped** (either `streamable_http_server` or `sse_server`).

---

## 1 · Install dependencies

Everything lives in one file now:

```bash
# inside an activated venv
pip install -r requirements.txt
```

## 2 · Run local transports only
```bash
pytest tests -q
```

## 3 - Run local & remote transports
```bash
MCP_SERVER_URL=$(heroku info -s -a "$APP_NAME" | grep web_url | cut -d= -f2 | tr -d '\n') \
API_KEY=$(heroku config:get API_KEY -a "$APP_NAME") \
pytest tests -q
```