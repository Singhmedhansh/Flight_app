from ..models.flight import Flight
from ..config.database_config import get_db_connection # type: ignore

class FlightController:
    def search_flights(self, origin, destination):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Flight WHERE origin=%s AND destination=%s", (origin, destination))
        flights = [Flight(**row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return flights