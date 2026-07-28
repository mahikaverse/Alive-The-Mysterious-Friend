"""FastAPI application factory.

Creates and configures the FastAPI application instance
with middleware, exception handlers, lifecycle hooks,
and environment-aware setup.
"""

import logging
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend import __app_name__, __description__, __version__
from backend.api.exceptions import (
    AppException,
    BadRequestException,
    InternalErrorException,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
)
from backend.api.middleware import AuthMiddleware, RequestContextMiddleware
from backend.api.routes import router
from backend.config.log_config import setup_logging
from backend.config.settings import settings, validate_settings
from backend.controllers.conversation_controller import ConversationController
from backend.behaviour.emotion_engine import EmotionEngine
from backend.behaviour.life_simulator import LifeSimulator
from backend.behaviour.relationship_engine import RelationshipEngine
from backend.controllers.module_adapters import (
    IdentityEngineAdapter,
    LLMProviderAdapter,
    PromptBuilderAdapter,
    ResponseValidatorAdapter,
)
from backend.database.connection import DatabaseConnection
from backend.memory.embeddings import Embeddings
from backend.memory.importance import ImportanceScorer
from backend.memory.memory_manager import MemoryManager
from backend.memory.memory_store import MemoryStore
from backend.memory.ranking import MemoryRanking
from backend.memory.retrieval import MemoryRetrieval

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and return a configured FastAPI application."""
    setup_logging()

    app = FastAPI(
        title=__app_name__,
        description=__description__,
        version=__version__,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # --- middleware (order matters) ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(AuthMiddleware)

    # --- singleton services ---
    # Database
    db_connection = DatabaseConnection(settings.database_url)
    try:
        db_connection.connect()
    except Exception as exc:
        logger.warning("Database connection failed — memory will be disabled: %s", exc)

    # Memory subsystem
    memory_manager = None
    try:
        embeddings = Embeddings(
            api_key=settings.openai_api_key,
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
        )
        memory_store = MemoryStore(
            embeddings=embeddings,
            db=db_connection,
            chroma_path=settings.chroma_path,
            collection_name=settings.chroma_collection,
        )
        retrieval = MemoryRetrieval(store=memory_store, embeddings=embeddings)
        scorer = ImportanceScorer(threshold=settings.memory_importance_threshold)
        ranking = MemoryRanking()
        memory_manager = MemoryManager(
            embeddings=embeddings,
            store=memory_store,
            retrieval=retrieval,
            scorer=scorer,
            ranking=ranking,
            top_k=settings.memory_top_k,
        )
        logger.info("Memory subsystem initialized successfully")
    except Exception as exc:
        logger.warning("Memory subsystem initialization failed: %s", exc)

    app.state.db = db_connection
    app.state.orchestrator = ConversationController(
        memory=memory_manager,
        emotion=EmotionEngine(),
        relationship=RelationshipEngine(),
        life=LifeSimulator(),
        persona=IdentityEngineAdapter(),
        prompt_builder=PromptBuilderAdapter(),
        llm=LLMProviderAdapter(),
        validator=ResponseValidatorAdapter(),
    )
    app.state.start_time = __import__("time").time()

    # --- exception handlers ---
    @app.exception_handler(BadRequestException)
    async def bad_request_handler(request: Request, exc: BadRequestException) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": exc.detail})

    @app.exception_handler(UnauthorizedException)
    async def unauthorized_handler(request: Request, exc: UnauthorizedException) -> JSONResponse:
        return JSONResponse(status_code=401, content={"error": exc.detail})

    @app.exception_handler(NotFoundException)
    async def not_found_handler(request: Request, exc: NotFoundException) -> JSONResponse:
        return JSONResponse(status_code=404, content={"error": exc.detail})

    @app.exception_handler(RateLimitException)
    async def rate_limit_handler(request: Request, exc: RateLimitException) -> JSONResponse:
        return JSONResponse(status_code=429, content={"error": exc.detail})

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning("App exception: %s", exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        logger.warning("Validation error: %s", exc)
        return JSONResponse(status_code=400, content={"error": str(exc)})

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error."},
        )

    # --- lifecycle ---
    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info(
            "%s v%s starting — environment=%s",
            __app_name__,
            __version__,
            settings.environment,
        )
        missing = validate_settings()
        if missing:
            logger.warning("Missing recommended settings: %s", ", ".join(missing))
            if settings.is_production:
                logger.error(
                    "Required settings missing in production: %s. Application may not function correctly.",
                    ", ".join(missing),
                )

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info(
            "%s v%s shutting down",
            __app_name__,
            __version__,
        )
        if hasattr(app.state, "db") and app.state.db is not None:
            app.state.db.disconnect()

    # --- routes ---
    app.include_router(router)

    return app
