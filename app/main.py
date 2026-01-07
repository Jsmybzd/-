from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.staticfiles import StaticFiles
from importlib import import_module
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.api import router as core_router
from app.visitor.api import router as visitor_router
from app.config import settings


class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/web/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

def _optional_router(module_path: str):
    try:
        mod = import_module(module_path)
        return getattr(mod, "router", None)
    except Exception:
        return None

app = FastAPI(
    title="国家公园智慧管理与生态保护系统 API",
    description="基于FastAPI的国家公园智慧管理系统 - 支持8种用户角色",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url=None,
)

frontend_dir = (Path(__file__).resolve().parent.parent / "frontend").resolve()
if frontend_dir.exists():
    app.mount("/web", StaticFiles(directory=str(frontend_dir), html=True), name="web")

# 添加缓存控制中间件
app.add_middleware(NoCacheMiddleware)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册所有路由
app.include_router(core_router, prefix="/api")
app.include_router(visitor_router, prefix="/api")

biodiversity_router = _optional_router("app.biodiversity.api")
if biodiversity_router:
    app.include_router(biodiversity_router, prefix="/api")

environment_router = _optional_router("app.environment.api")
if environment_router:
    app.include_router(environment_router, prefix="/api")

enforcement_router = _optional_router("app.enforcement.api")
if enforcement_router:
    app.include_router(enforcement_router, prefix="/api")

research_router = _optional_router("app.research.api")
if research_router:
    app.include_router(research_router, prefix="/api")


@app.get("/")
async def root():
    """根路由 - 重定向到前端登录页"""
    return RedirectResponse(url="/web/login.html")


@app.get("/api/redoc", include_in_schema=False)
async def redoc():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://unpkg.com/redoc@2.0.0/bundles/redoc.standalone.js",
    )


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}