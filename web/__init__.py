"""Satya web: Jinja2 + HTMX + Alpine pages. Mount `router` (pages) and `assets_router` (static) in asgi.py."""

from fastapi import APIRouter

from web import account, audits, auth, checker, review
from web.assets import router as assets_router

router = APIRouter()
router.include_router(auth.router)
router.include_router(account.public)
router.include_router(account.protected)
router.include_router(account.setup_router)
router.include_router(checker.router)
router.include_router(review.router)
router.include_router(audits.router)

__all__ = ["assets_router", "router"]
