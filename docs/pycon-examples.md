*MAGIC*
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://www.heroku.com/deploy?template=https://github.com/heroku/mcp-code-exec-python)


## Local STDIO
There are two ways to easily test out your MCP server in STDIO mode:

### 1. Local STDIO - Example Python STDIO Client
List tools:
```bash
python example_clients/test_stdio.py mcp list_tools | jq
```

Example tool call request:
```bash
python example_clients/test_stdio.py mcp call_tool --args '{
  "name": "code_exec_python",
  "arguments": {
    "code": "import numpy as np; print(np.random.rand(50).tolist())",
    "packages": ["numpy"]
  }
}' | jq
```

### 2. Local STDIO - Direct Calls
Example tool call request:
```bash
cat <<EOF | python -m src.stdio_server

{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"0.1.0","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}

{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}

{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"code_exec_python","arguments":{"code":"import numpy as np; print(np.random.rand(50).tolist())","packages":["numpy"]}}}
EOF
```
*(Note that the server expects the client to send a shutdown request, so you can stop the connection with CTRL-C)*


## Local SSE
One-time packages installation:
```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

If you're testing SSE, in one terminal pane you'll need to start the server:
```
source venv/bin/activate
export API_KEY=$(heroku config:get API_KEY -a $APP_NAME)
uvicorn src.sse_server:app --reload
```
*Running with --reload is optional, but great for local development*

Next, in a new pane, you can try running some queries against your server:
### Local SSE - Example Requests
First run:
```bash
export API_KEY=$(heroku config:get API_KEY -a $APP_NAME)
```

List tools:
```bash
python example_clients/test_sse.py mcp list_tools | jq
```

Example tool call request:
*NOTE: this will intentionally NOT work if you have set `STDIO_MODE_ONLY` to `true`.*
```bash
python example_clients/test_sse.py mcp call_tool --args '{
  "name": "code_exec_python",
  "arguments": {
    "code": "import numpy as np; print(np.random.rand(50).tolist())",
    "packages": ["numpy"]
  }
}' | jq
```

## Remote SSE
To test your remote `SSE` server, you'll need to make sure a web process is actually spun up. To save on costs, by default this repository doesn't spin up web dynos on creation, as many folks only want to use `STDIO` mode (local and one-off dyno) requests:
```
heroku ps:scale web=1 -a $APP_NAME
```
You only need to do this once, unless you spin back down to 0 web dynos to save on costs (`heroku ps:scale web=0 -a $APP_NAME`). To confirm currently running dynos, use `heroku ps -a $APP_NAME`.

Next, run:

```bash
export API_KEY=$(heroku config:get API_KEY -a $APP_NAME)
export MCP_SERVER_URL=$(heroku info -s -a $APP_NAME | grep web_url | cut -d= -f2)
```

Next, you can run the same queries as shown in the [Local SSE - Example Requests](#local-sse---example-requests) testing section - because you've set `MCP_SERVER_URL`, the client will call out to your deployed server.


### Cool, but, uh - maybe a bad idea?

--> Solution?
[Working With MCP On Heroku](https://devcenter.heroku.com/articles/heroku-inference-working-with-mcp)
```bash
heroku ai:models:create claude-3-7-sonnet -a $APP_NAME
heroku config -a $APP_NAME

export INFERENCE_URL=$(heroku config:get INFERENCE_URL -a $APP_NAME)
export INFERENCE_KEY=$(heroku config:get INFERENCE_KEY -a $APP_NAME)
```

[`v1/mcp/servers`](https://devcenter.heroku.com/articles/heroku-inference-api-v1-mcp-servers) keeps track of all your tools:
```bash
curl $INFERENCE_URL/v1/mcp/servers -H "Authorization: Bearer $INFERENCE_KEY" | jq
```

[`v1/agents/heroku`](https://devcenter.heroku.com/articles/heroku-inference-api) has access to your registered tools:
```bash
curl "$INFERENCE_URL/v1/agents/heroku" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $INFERENCE_KEY" \
  -H "X-Forwarded-Proto: https" \
  -d @- <<EOF
{
  "model": "claude-3-7-sonnet",
  "messages": [
    {
      "role": "user",
      "content": "What is the input schema to the code exec tool? Give me the raw json schema, no need to call the tool"
    }
  ],
  "tools": [
    {
      "type": "mcp",
      "name": "code_exec_python"
    }
  ]
}
EOF
```

Next let's actually call the tool:
```bash
curl "$INFERENCE_URL/v1/agents/heroku" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $INFERENCE_KEY" \
  -H "X-Forwarded-Proto: https" \
  -d @- <<EOF
{
  "model": "claude-3-7-sonnet",
  "messages": [
    {
      "role": "user",
      "content": "What is the sha256 of the string 'Purple Python'?"
    }
  ],
  "tools": [
    {
      "type": "mcp",
      "name": "code_exec_python"
    }
  ]
}
EOF
```

You also get access to native built-in [`heroku_tools`](https://devcenter.heroku.com/articles/heroku-inference-tools):
```bash
curl "$INFERENCE_URL/v1/agents/heroku" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $INFERENCE_KEY" \
  -H "X-Forwarded-Proto: https" \
  -d @- <<EOF
{
  "model": "claude-3-7-sonnet",
  "messages": [
    {
      "role": "user",
      "content": "Tell me about this file - https://www.melbpc.org.au/wp-content/uploads/2017/10/small-example-pdf-file.pdf"
    }
  ],
  "tools": [
    {
      "type": "heroku_tool",
      "name": "html_to_markdown"
    },
    {
      "type": "heroku_tool",
      "name": "pdf_to_markdown"
    }
  ]
}
EOF
```