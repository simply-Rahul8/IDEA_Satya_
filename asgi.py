"""ASGI entry point (Vercel bom1 / uvicorn). Routers from api/ and web/ mount here."""

from fastapi import FastAPI

from web import assets_router
from web import router as web_router
from web.security import SessionMiddleware

app = FastAPI(title="Satya", version="0.0.0", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(SessionMiddleware)
app.include_router(assets_router)
app.include_router(web_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
