# End-to-End Test Suite (`tests/`)

You know what's better than unit tests? End to end integration tests.

These pytest tests run **every MCP transport** this repo supports, both locally and (optionally) against a deployed Heroku app.

| Context ID        | Transport exercised                                       | Needs running **web** dyno? |
|-------------------|-----------------------------------------------------------|-----------------------------|
| `http_local`      | Streamable HTTP on `localhost:8000/mcp/`                  | — |
| `sse_local`       | SSE on `localhost:8000/mcp/sse`                           | — |
| `stdio_local`     | STDIO (example client boots its own server)               | — |
| `remote`          | Transport named in **`$REMOTE_SERVER_TRANSPORT_MODULE`**&nbsp;(`streamable_http_server` or `sse_server`) served by your web dyno | **Yes** |
| `remote_stdio`    | STDIO via a **one-off Heroku dyno**                       | **No** – works even at `web=0` |

*If the web dyno is asleep or scaled to `0`, the `remote` tests auto-skip.
`remote_stdio` still runs, because it spins up its own one-off dyno.*

To scale up the number of web dynos running in your app to 1, run:
```bash
heroku ps:scale web=1 -a "$APP_NAME"
```

---

## 1 · Install dependencies

```bash
# inside an activated venv
pip install -r requirements.txt
```

## 2 · Run local transports only
```bash
git push heroku <your-branch>:main
```

## 2 · Run local & one-off-dyno (STDIO) deployed transports
```bash
pytest tests -q
```

## 3 - Run local & all deployed transports
```bash
REMOTE_SERVER_TYPE=$(heroku config:get REMOTE_SERVER_TYPE) \
MCP_SERVER_URL=$(heroku info -s -a "$APP_NAME" | grep web_url | cut -d= -f2 | tr -d '\n') \
API_KEY=$(heroku config:get API_KEY -a "$APP_NAME") \
pytest tests -q
```

*NOTE: if your `REMOTE_SERVER_TYPE` is set to `sse_server` and not the default `streamable_http_server`, you'll need to change the `REMOTE_SERVER_TRANSPORT_MODULE` declaration line in `.github/workflows/test.yml` to make sure that the end to end integration tests against the temporary deployed remote server are using the appropriate client code.*