from fastapi import FastAPI
from src.interfaces.api.routes import events, chat
from src.infrastructure.database.postgres import PostgresEventRepository
from src.core.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI(title="Calendar Planning Assistant")

# Include routers
app.include_router(events.router)
app.include_router(chat.router)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and create tables on startup"""
    try:
        # Initialize database connection and create tables
        repo = PostgresEventRepository()
        # Create table
        with repo.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id SERIAL PRIMARY KEY,
                    event_name VARCHAR(255) NOT NULL,
                    event_description TEXT,
                    event_start_date_time TIMESTAMP NOT NULL,
                    event_end_date_time TIMESTAMP NOT NULL,
                    event_location VARCHAR(255)
                )
                """
            )
            repo.conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
