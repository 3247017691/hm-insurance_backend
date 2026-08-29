import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app import settings
from app.core import configure_logging, get_logger
from app.core.exceptions import ApplicationError
from app.core.lifespan import lifespan
from app.modules.chat_thread.exceptions import ChatThreadNotFoundError
from app.modules.product.router import router as product_router
from app.modules.chat_thread.router import router as chat_thread_router
from app.modules.chat.router import router as chat_router
import sys
from app.agents.insurance_advisor import init_insurance_agent
from app.infra.checkpointer import (
    close_checkpointer,
    init_checkpointer,
)

app = FastAPI(
    title=settings.app.name,
    debug=settings.app.debug,
    lifespan=lifespan,
)

app.include_router(chat_thread_router)
app.include_router(product_router)
app.include_router(chat_router)

configure_logging(settings.log.level)
logger = get_logger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", summary='健康检测端口')
def health_check() -> dict[str, str]:
    logger.info("执行检查")
    return {'status':'ok'}

# 统一处理异常信息，发现是ChatThreadNotFound，返回对应的错误状态码和错误信息
@app.exception_handler(ApplicationError)
def handle_exception(request: Request, exc: ApplicationError) -> JSONResponse:
    logger.error(f"处理异常, 请求路径: {request.url}, 异常信息: {exc}")
    return JSONResponse(
        status_code=exc.status_code,# http状态码
        content={
            "code": exc.code, #项目自定义的状态码
            "message": exc.message
        }
    )


if __name__ == '__main__':
    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=False,
        loop="asyncio:SelectorEventLoop" if sys.platform == "win32" else "auto",
    )