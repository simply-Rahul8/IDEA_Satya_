"""Satya web: Jinja2 + HTMX + Alpine pages. Mount `router` (pages) and `assets_router` (static) in asgi.py."""

from fastapi import APIRouter

from web import checker, demo, review
from web.assets import router as assets_router

router = APIRouter()
router.include_router(checker.router)
router.include_router(review.router)
demo.seed()  # preview only: Platform replaces the store and removes this

__all__ = ["assets_router", "router"]
