"""AI Learn 后端服务入口。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, engine
from .routers import chat, prompt, sessions

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 轻量项目直接用 create_all 建表；后续需要迁移可接入 Alembic
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Vue3 + Element Plus 前端的问答服务，模型与数据库只在后端访问。",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(prompt.router, prefix="/api")


@app.get("/api/health", tags=["system"], summary="健康检查")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "model": settings.mimo_model or "未配置",
        "mock_llm": settings.mock_llm,
    }
