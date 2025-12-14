import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph
from loguru import logger
from starlette.responses import StreamingResponse

from app.graph.builder import build_graph_with_memory
from app.graph.state import InputState

# --- 2. 路径配置 ---

# src/app/api
BASE_DIR = Path(__file__).resolve().parent
# src/app/templates
TEMPLATES_DIR = BASE_DIR.parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

graph: Optional[CompiledStateGraph] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph
    try:
        graph = build_graph_with_memory()
        print("✅ LangGraph 加载完成！")
    except Exception as e:
        print(f"❌ LangGraph 加载失败: {e}")
    yield


app = FastAPI(title="LangGraph Agent Server", lifespan=lifespan)

# 设置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def get_frontend(request: Request):
    """
    加载前端页面
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/langgraph/query")
async def langgraph_query(
        query: str = Form(...),
        user_id: int = Form(...),
        conversation_id: Optional[str] = Form(None),
):
    try:
        # 1. 准备 Thread ID
        thread_id = conversation_id if conversation_id else str(uuid.uuid4())
        thread_config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}

        # 2. 构造输入 (包装成 HumanMessage 更规范)
        # 这样 LangGraph 明确知道这是一条用户发来的新消息
        input_message = HumanMessage(content=query)
        input_state = {"messages": [input_message]}

        # 3. 流式处理
        async def process_stream():
            async for msg, metadata in graph.astream(
                    input=input_state,
                    stream_mode="messages",
                    config=thread_config,
            ):
                if msg.content:
                    # 序列化内容
                    content_json = json.dumps(msg.content, ensure_ascii=False)
                    yield f"data: {content_json}\n\n"

        response = StreamingResponse(process_stream(), media_type="text/event-stream")
        response.headers["X-Conversation-ID"] = thread_id
        return response

    except Exception as e:
        logger.error(f"LangGraph query error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000)
