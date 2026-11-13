"""ASGI entry point (Vercel bom1 / uvicorn). Routers from api/ and web/ mount here."""

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import PlainTextResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from web import assets_router
from web import router as web_router
from web.app import render
from web.security import SecurityHeadersMiddleware, SessionMiddleware

app = FastAPI(title="Satya", version="0.0.0", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(SessionMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# What a person sees for each error. API-style calls (htmx, forms, fetch) keep the plain status and detail.
_ERROR_PAGES = {
    403: ("Request refused", "This page didn't accept that request. Reload it and try again."),
    404: ("Page not found", "There's nothing at this address."),
    405: ("Page not found", "There's nothing at this address."),
    429: ("Too many requests", "Wait a minute, then try again."),
    500: ("Something broke on our side", "It's been logged. Try again in a moment."),
    503: ("Not open yet", "Sign-in and the brand workspace aren't open to the public yet. The claim checker is."),
}


def _wants_page(request: Request) -> bool:
    """A browser loading a page, not an htmx swap or a script."""
    return (
        request.method == "GET"
        and "text/html" in request.headers.get("accept", "")
        and "hx-request" not in request.headers
    )


def _error_page(request: Request, status: int):
    heading, text = _ERROR_PAGES[status]
    ctx = {"code": status, "heading": heading, "text": text, "title": f"{heading} · Satya"}
    return render(request, "errors/page.html", ctx, status=status)


@app.exception_handler(StarletteHTTPException)
async def http_errors(request: Request, exc: StarletteHTTPException):
    """A signed-out browser page load goes to sign-in; other browser page loads get a designed error page."""
    if exc.status_code == 401 and _wants_page(request):
        return RedirectResponse("/signin", status_code=303, headers={"Cache-Control": "no-store"})
    if exc.status_code in _ERROR_PAGES and _wants_page(request):
        return _error_page(request, exc.status_code)
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def server_error(request: Request, exc: Exception):
    """Unhandled errors: a page for browsers, plain text otherwise. Starlette still re-raises, so it is logged."""
    if _wants_page(request):
        return _error_page(request, 500)
    return PlainTextResponse("Internal Server Error", status_code=500)


app.include_router(assets_router)
app.include_router(web_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
