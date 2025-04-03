
# Heroku MCP Code Execution - Python

- [Heroku MCP Code Execution - Python](#heroku-mcp-code-execution---python)
  - [Automatic Deployment](#automatic-deployment)
  - [Manual Deployment](#manual-deployment)
    - [**Set Required Environment Variables from Heroku CLI**](#set-required-environment-variables-from-heroku-cli)
  - [Local Testing](#local-testing)
    - [Local SSE](#local-sse)
    - [Local STDIO](#local-stdio)
      - [1. Example Python STDIO Client](#1-example-python-stdio-client)
      - [2. Direct Calls](#2-direct-calls)
  - [Remote Testing](#remote-testing)
    - [Remote SSE](#remote-sse)
      - [List Tools](#list-tools)
      - [code\_exec\_python](#code_exec_python)
    - [Remote STDIO](#remote-stdio)
      - [1. Example Python STDIO Client, Running On-Server](#1-example-python-stdio-client-running-on-server)
      - [2. Direct Calls](#2-direct-calls-1)
    - [3. Coming Soon - Heroku MCP Gateway!](#3-coming-soon---heroku-mcp-gateway)

## Automatic Deployment

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://www.heroku.com/deploy)

## Manual Deployment
### **Set Required Environment Variables from Heroku CLI**
Instead of manually setting each variable, use the Heroku CLI to pull the correct values.

```sh
export APP_NAME=<your-heroku-app-name>
heroku create $APP_NAME

heroku buildpacks:set heroku/python -a $APP_NAME
heroku config:set WEB_CONCURRENCY=1 -a $APP_NAME
# set a private API key that you create, for example:
heroku config:set API_KEY=$(openssl rand -hex 32) -a $APP_NAME
heroku config:set STDIO_MODE_ONLY=<true/false>
```

*Note: we recommend setting `STDIO_MODE_ONLY` to `true` for security and code execution isolation security.*

Also put these config variables into a local .env file for local development:
```
heroku config -a $APP_NAME --shell | tee .env > /dev/null
```

Next, connect your app to your git repo:
```
heroku git:remote -a $APP_NAME
```
And deploy!
```
git push heroku main
```
View logs with:
```
heroku logs --tail -a $APP_NAME
```

## Local Testing
### Local SSE
One-time packages installation:
```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

If you're testing SSE, in one terminal pane you'll need to run:
```
source venv/bin/activate
```
And then to run the SSE server:
```
uvicorn src.sse_server:app --reload
```
*Running with --reload is optional, but great for local development*

Next, in a new pane, you can run the same queries as shown in the [Remote SSE](#remote-sse) testing section - just don't set the `MCP_SERVER_URL`, or set it to `export MCP_SERVER_URL=http://localhost:8000/`

### Local STDIO
There are two ways to easily test out your MCP server in STDIO mode:

#### 1. Example Python STDIO Client
List tools:
```
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

#### 2. Direct Calls
```bash
cat <<EOF | python -m src.stdio_server
Content-Length: 148

{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"0.1.0","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}
Content-Length: 66

{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}
Content-Length: 205

{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"code_exec_python","arguments":{"code":"import numpy as np; print(np.random.rand(50).tolist())","packages":["numpy"]}}}
EOF
```
*(Note that the server expects the client to send a shutdown request, so you can stop the connection with CTRL-C)*

## Remote Testing
```bash
export API_KEY=$(heroku config:get API_KEY -a $APP_NAME)
export MCP_SERVER_URL=$(heroku info -s -a $APP_NAME | grep web_url | cut -d= -f2)
```

### Remote SSE
#### List Tools
```bash
python example_clients/test_sse.py mcp list_tools | jq
```

####  code_exec_python
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

Remember, this will run your local MCP server if `MCP_SERVER_URL` is unset, otherwise it will run against your remote `MCP_SERVER_URL` server.

### Remote STDIO
There are two ways to test out your remote MCP server in STDIO mode:

#### 1. Example Python STDIO Client, Running On-Server
To run against your deployed code, you can run the example client code on your deployed server:
```bash
heroku run --app $APP_NAME -- bash -c 'python -m example_clients.test_stdio mcp list_tools | jq'
```
or:
```bash
heroku run --app $APP_NAME -- bash -c '
python -m example_clients.test_stdio mcp call_tool --args '\''{
  "name": "code_exec_python",
  "arguments": {
    "code": "import numpy as np; print(np.random.rand(50).tolist())",
    "packages": ["numpy"]
  }
}'\'' | jq
'
```

#### 2. Direct Calls
Or, you can also run or simulate a client locally that sends your client-side requests to the one-off dynos.

Example code-execution command (installs packages and runs command in an isolated, one-off heroku dyno).
```bash
heroku run --app "$APP_NAME" -- bash -c "python -m src.stdio_server 2> logs.txt" <<EOF
Content-Length: 148

{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"0.1.0","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}
Content-Length: 66

{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}
Content-Length: 205

{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"code_exec_python","arguments":{"code":"import numpy as np; print(np.random.rand(50).tolist())","packages":["numpy"]}}}
EOF
```

Again, note that since we're running our request through a single command, we're unable to simulate a client's shutdown request.

### 3. Coming Soon - Heroku MCP Gateway!
Soon, you'll also be able to connect up your MPC repo to Heroku's MCP Gateway, which will make streaming requests and responses from one-off MCP dynos simple!

The Heroku MCP Gateway will implement a rendezvous protocol so that you can easily talk to your MCP server one-off dynos (code execution isolation!) with seamless back-and-forth communication.
