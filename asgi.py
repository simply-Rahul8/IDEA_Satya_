"""ASGI entry point (Vercel bom1 / uvicorn). Routers from api/ and web/ mount here."""

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from web import assets_router
from web import router as web_router
from web.security import SessionMiddleware

app = FastAPI(title="Satya", version="0.0.0", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(SessionMiddleware)


@app.exception_handler(StarletteHTTPException)
async def signed_out_to_sign_in(request: Request, exc: StarletteHTTPException):
    """A signed-out browser page load goes to sign-in; API-style calls (htmx, forms, fetch) keep the plain 401."""
    if (
        exc.status_code == 401
        and request.method == "GET"
        and "text/html" in request.headers.get("accept", "")
        and "hx-request" not in request.headers
    ):
        return RedirectResponse("/signin", status_code=303, headers={"Cache-Control": "no-store"})
    return await http_exception_handler(request, exc)


app.include_router(assets_router)
app.include_router(web_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
