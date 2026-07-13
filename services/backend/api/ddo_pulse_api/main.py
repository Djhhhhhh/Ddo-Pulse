"""FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ddo_pulse_core.web_config import load_web_config

from ddo_pulse_api.api_routes import router
from ddo_pulse_api.scheduler import create_and_start_scheduler, shutdown_scheduler

_SERVICES_ROOT = Path(__file__).resolve().parents[3]
_WEB_DIST = _SERVICES_ROOT / "web" / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_and_start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(title="Ddo-Pulse API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8765",
        "http://localhost:8765",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/api")
def api_root() -> dict[str, str]:
    return {"service": "ddo-pulse", "docs": "/docs"}


def _mount_frontend() -> None:
    if not _WEB_DIST.is_dir():
        return

    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request as StarletteRequest

    _INDEX = _WEB_DIST / "index.html"

    class SpaFallbackMiddleware(BaseHTTPMiddleware):
        """SPA 兜底：静态文件 404 时返回 index.html"""

        async def dispatch(self, request: StarletteRequest, call_next):
            response = await call_next(request)
            if response.status_code == 404 and not request.url.path.startswith("/api"):
                if _INDEX.is_file():
                    return FileResponse(_INDEX)
            return response

    app.add_middleware(SpaFallbackMiddleware)
    app.mount("/", StaticFiles(directory=_WEB_DIST, html=True), name="frontend")


_mount_frontend()


def run() -> None:
    import uvicorn

    cfg = load_web_config()
    api_cfg = cfg.get("api") or {}
    host = str(api_cfg.get("host", "127.0.0.1"))
    port = int(api_cfg.get("port", 8765))
    uvicorn.run(
        "ddo_pulse_api.main:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    run()
