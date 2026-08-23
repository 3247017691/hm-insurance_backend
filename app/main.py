import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app import settings
from app.core import configure_logging, get_logger
from app.core.lifespan import lifespan

configure_logging(settings.logging.level)
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app.name,
    debug=settings.app.debug,
    lifespan=lifespan,
)

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

if __name__ == '__main__':
    uvicorn.run(
        'app.main:app',
        host=settings.app.host,
        port=settings.app.port,
        reload=False
    )