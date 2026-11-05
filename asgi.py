"""ASGI entry point (Vercel bom1 / uvicorn). Routers from api/ and web/ mount here."""

from fastapi import FastAPI

app = FastAPI(title="Satya", version="0.0.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
