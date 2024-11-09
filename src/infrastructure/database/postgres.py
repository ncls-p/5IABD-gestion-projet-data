import psycopg2
from typing import List
from ...core.config import get_settings
from ...domain.entities.event import Event
from ...domain.interfaces.repositories import EventRepository
from ...core.logger import setup_logger

settings = get_settings()
logger = setup_logger(__name__)


class PostgresEventRepository(EventRepository):
    def __init__(self):
        self.conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            database=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            port=settings.POSTGRES_PORT,
        )

    async def create(self, event: Event) -> Event:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO calendar_events 
                (event_name, event_description, event_start_date_time, event_end_date_time, event_location)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    event.event_name,
                    event.event_description,
                    event.event_start_date_time,
                    event.event_end_date_time,
                    event.event_location,
                ),
            )
            result = cur.fetchone()
            if result is None:
                raise ValueError("Failed to create event - no ID returned")

            event_id = result[0]
            self.conn.commit()

            # Create a new Event instance with the ID
            return Event(
                id=event_id,
                event_name=event.event_name,
                event_description=event.event_description,
                event_start_date_time=event.event_start_date_time,
                event_end_date_time=event.event_end_date_time,
                event_location=event.event_location,
            )
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error creating event: {str(e)}")
            raise
        finally:
            cur.close()

    async def get_all(self) -> List[Event]:
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT * FROM calendar_events")
            rows = cur.fetchall()
            return [
                Event(
                    id=row[0],
                    event_name=row[1],
                    event_description=row[2],
                    event_start_date_time=row[3],
                    event_end_date_time=row[4],
                    event_location=row[5],
                )
                for row in rows
            ]
        finally:
            cur.close()

    async def delete(self, event_id: int) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute("DELETE FROM calendar_events WHERE id = %s", (event_id,))
            deleted = cur.rowcount > 0
            self.conn.commit()
            return deleted
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error deleting event: {str(e)}")
            raise
        finally:
            cur.close()

    def __del__(self):
        if hasattr(self, "conn"):
            self.conn.close()
