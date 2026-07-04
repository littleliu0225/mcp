from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
import json, io, sys, traceback, httpx

app = FastAPI()

tools = [
    {
        "name": "run_python_code",
        "description": "安全执行python代码",
        "inputSchema": {
            "type": "object",
            "properties": {"code": {"type": "string"}}
        }
    },
    {
        "name": "fetch_url",
        "description": "读取网页文本",
        "inputSchema": {
            "type": "object",
            "properties": {"url": {"type": "string"}}
        }
    }
]

def run_code(code):
    buf = io.StringIO()
    sys.stdout = buf
    try:
        exec(code, {"__builtins__": __builtins__})
    except Exception as e:
        return traceback.format_exc()
    finally:
        sys.stdout = sys.__stdout__
    return buf.getvalue()

def fetch_page(url):
    r = httpx.get(url, timeout=8)
    return r.text[:5000]

async def sse_generator(request: Request):
    yield json.dumps({"type": "ready", "tools": tools})
    while True:
        if await request.is_disconnected():
            break

@app.get("/mcp/sse")
async def sse_endpoint(request: Request):
    return EventSourceResponse(sse_generator(request))

@app.post("/mcp/call")
async def call_tool(body: dict):
    name = body.get("name")
    args = body.get("arguments", {})
    if name == "run_python_code":
        return {"result": run_code(args["code"])}
    if name == "fetch_url":
        return {"result": fetch_page(args["url"])}
    return {"result": "unknown tool"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
