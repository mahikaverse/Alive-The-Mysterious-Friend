"""Database connection management.

Creates and manages the SQLAlchemy engine, session factory,
and provides dependency-injection helpers.
"""

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import Base

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database engine and session lifecycle.

    Usage::

        db = DatabaseConnection("postgresql://user:pass@host/db")
        db.connect()
        session = db.get_session()
        ...
        db.disconnect()
    """

    def __init__(self, database_url: str | None = None) -> None:
        self._database_url: str = database_url or ""
        self._engine = None
        self._session_factory: sessionmaker | None = None

    def connect(self, database_url: str | None = None) -> None:
        """Establish a connection to the database and create tables.

        Parameters
        ----------
        database_url : str | None
            Override the connection string. Falls back to the URL
            provided at construction time.
        """
        url = database_url or self._database_url
        if not url:
            logger.warning("No database URL provided — skipping database connection")
            return

        try:
            connect_args = {}
            engine_kwargs = {
                "pool_pre_ping": True,
                "echo": False,
            }

            if not url.startswith("sqlite"):
                engine_kwargs["pool_size"] = 5
                engine_kwargs["max_overflow"] = 10
            else:
                connect_args["check_same_thread"] = False

            self._engine = create_engine(
                url,
                connect_args=connect_args,
                **engine_kwargs,
            )
            self._session_factory = sessionmaker(bind=self._engine)

            Base.metadata.create_all(self._engine)

            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info("Database connected successfully")
        except Exception as exc:
            logger.error("Database connection failed: %s", exc)
            self._engine = None
            self._session_factory = None
            raise

    def disconnect(self) -> None:
        """Close the database connection gracefully."""
        if self._engine is not None:
            try:
                self._engine.dispose()
                logger.info("Database connection closed")
            except Exception as exc:
                logger.warning("Error closing database: %s", exc)
            finally:
                self._engine = None
                self._session_factory = None

    def get_session(self) -> Session | None:
        """Return a new database session.

        Returns
        -------
        Session | None
            A new SQLAlchemy session, or None if not connected.
        """
        if self._session_factory is None:
            logger.warning("Database not connected — returning None")
            return None
        return self._session_factory()

    @property
    def is_connected(self) -> bool:
        """Check if the database connection is active."""
        return self._engine is not None
