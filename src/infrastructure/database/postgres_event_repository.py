import psycopg2
from typing import Optional, List
from ...domain.entities.event import Event
from ...domain.repositories.event_repository import EventRepository


class PostgresEventRepository(EventRepository):
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432",
        )

    async def get_all(self) -> List[Event]:
        with self.conn.cursor() as cur:
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

    async def get_by_id(self, event_id: int) -> Optional[Event]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM calendar_events WHERE id = %s", (event_id,))
            row = cur.fetchone()
            if row:
                return Event(
                    id=row[0],
                    event_name=row[1],
                    event_description=row[2],
                    event_start_date_time=row[3],
                    event_end_date_time=row[4],
                    event_location=row[5],
                )
            return None

    async def create(self, event: Event) -> Event:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO calendar_events (
                    event_name, event_description, event_start_date_time,
                    event_end_date_time, event_location
                ) VALUES (%s, %s, %s, %s, %s) RETURNING id
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
                raise ValueError("Failed to create event: No ID returned")
            event.id = result[0]
            self.conn.commit()
            return event

    async def delete(self, event_id: int) -> bool:
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM calendar_events WHERE id = %s RETURNING id", (event_id,)
            )
            self.conn.commit()
            return cur.rowcount > 0
