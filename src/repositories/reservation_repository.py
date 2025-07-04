from config.database_config import get_db_connection #type: ignore

class ReservationRepository:
    def __init__(self):
        self.connection = get_db_connection()
        self.cursor = self.connection.cursor()

    def close(self):
        self.cursor.close()
        self.connection.close()

    def get_reservation(self, reservation_number):
        query = "SELECT * FROM FlightReservation WHERE reservation_number = %s"
        self.cursor.execute(query, (reservation_number,))
        return self.cursor.fetchone()

    def get_reservations_by_user(self, user):
        username = user.username
        get_user_id_query = """
            SELECT account_id FROM account
            WHERE username = %s
        """
        self.cursor.execute(get_user_id_query, (username,))
        user_id_result = self.cursor.fetchone()

        if user_id_result:
            user_id = user_id_result[0]
            query = """
                SELECT * FROM FlightReservation
                WHERE user_id = %s
            """
            self.cursor.execute(query, (user_id,))
            return self.cursor.fetchall()
        else:
            return None

    def cancel_reservation(self, reservation_number):
        get_reservation_query = """
            SELECT flight_no, seats
            FROM FlightReservation
            WHERE reservation_number = %s
        """
        self.cursor.execute(get_reservation_query, (reservation_number,))
        reservation = self.cursor.fetchone()

        if reservation:
            flight_no, seats = reservation
            delete_reservation_query = """
                DELETE FROM FlightReservation
                WHERE reservation_number = %s
            """
            self.cursor.execute(delete_reservation_query, (reservation_number,))
            update_flight_query = """
                UPDATE Flight
                SET booked_seats = booked_seats - %s
                WHERE flight_no = %s
            """
            self.cursor.execute(update_flight_query, (seats, flight_no))
            self.connection.commit()
            print(f"Reservation {reservation_number} has been successfully canceled and deleted.")
        else:
            print(f"Reservation {reservation_number} not found.")

    def create_reservation(self, user, flight_no, seats, creation_date, payment_amount):
        username = user.username
        get_user_id_query = """
            SELECT account_id FROM account
            WHERE username = %s
        """
        self.cursor.execute(get_user_id_query, (username,))
        user_id_result = self.cursor.fetchone()

        if user_id_result:
            user_id = user_id_result[0]
            query = """
                INSERT INTO FlightReservation (user_id, flight_no, seats, creation_date, payment_amount)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (user_id, flight_no, seats, creation_date, payment_amount))
            update_flight_query = """
                UPDATE Flight
                SET booked_seats = booked_seats + %s
                WHERE flight_no = %s
            """
            self.cursor.execute(update_flight_query, (seats, flight_no))
            self.connection.commit()
        else:
            print(f"User {username} not found. Reservation not created.")