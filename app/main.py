"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app import __version__
from app.api import (
    routes_collections,
    routes_eval,
    routes_graph,
    routes_health,
    routes_ingest,
    routes_query,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAGForge",
        version=__version__,
        description=(
            "A provider-agnostic Retrieval-Augmented Generation service: "
            "pluggable LLMs, embeddings and vector stores, hybrid retrieval "
            "and built-in answer evaluation."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(routes_health.router)
    app.include_router(routes_ingest.router)
    app.include_router(routes_query.router)
    app.include_router(routes_collections.router)
    app.include_router(routes_eval.router)
    app.include_router(routes_graph.router)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    return app


app = create_app()
