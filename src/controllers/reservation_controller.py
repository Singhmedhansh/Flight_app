import os
import sys
import heapq
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime
import mysql.connector

from models.flight import Flight
from models.flight_reservation import FlightReservation
from repositories.flight_repository import FlightRepository
from repositories.reservation_repository import ReservationRepository

__all__ = ['ReservationController']

class ReservationController:
    def __init__(self):
        self.connection = mysql.connector.connect(
            host="localhost",
            user="educative",
            password="BMWfav3$",
            database="flight"
        )
        self.flight_repo = FlightRepository()
        self.reservation_repo = ReservationRepository()

    def create_flight_object(self, flight_data):
        reordered_flight_data = flight_data[1:] + (flight_data[0],)
        return Flight(*reordered_flight_data)

    def view_reservations(self, user):
        reservations = self.reservation_repo.get_reservations_by_user(user)
        return reservations  # Return list of reservations

    def cancel_reservation(self, user, reservation_number):
        # Validate the input
        if not reservation_number:
            return {"success": False, "message": "Reservation number is required to cancel a reservation."}

        user_reservations = self.reservation_repo.get_reservations_by_user(user)
        # Optionally, check if reservation_number is in user_reservations

        try:
            self.reservation_repo.cancel_reservation(reservation_number)
            return {"success": True, "message": f"Reservation {reservation_number} has been successfully canceled."}
        except Exception as e:
            return {"success": False, "message": f"Error canceling reservation: {e}"}

    def process_payment(self, user, price):
        # Dummy payment processing logic to simulate successful payment
        # In a real app, integrate with a payment gateway here
        return True

    def make_reservation(self, user, num_seats, direct_flight=None, itinerary=None):
        # num_seats: int, from web form
        if direct_flight:
            available_seats = direct_flight.get_available_seats()
            if num_seats > available_seats:
                return {"success": False, "message": f"Sorry, only {available_seats} seats available for this flight."}
            total_price = float(direct_flight.get_ticket_price()) * num_seats
            self.reservation_repo.create_reservation(
                user=user,
                flight_no=direct_flight.get_flight_no(),
                seats=num_seats,
                creation_date=datetime.now(),
                payment_amount=total_price
            )
            return {"success": True, "message": f"Reservation for flight {direct_flight.get_flight_no()} made successfully.", "total_price": total_price}

        elif itinerary:
            total_price = 0
            all_available = True
            for flight in itinerary:
                available_seats = flight.get_available_seats()
                if num_seats > available_seats:
                    return {"success": False, "message": f"Sorry, only {available_seats} seats available for flight {flight.get_flight_no()}."}
                total_price += float(flight.get_ticket_price()) * num_seats

            for flight in itinerary:
                self.reservation_repo.create_reservation(
                    user=user,
                    flight_no=flight.get_flight_no(),
                    seats=num_seats,
                    creation_date=datetime.now(),
                    payment_amount=float(flight.get_ticket_price()) * num_seats
                )
            return {"success": True, "message": "Itinerary reservation made successfully.", "total_price": total_price}

        return {"success": False, "message": "No flight or itinerary provided."}

    def _find_cheapest_route(self, flights_or_itineraries, departure_airport, destination_airport):
        graph = {}
        for item in flights_or_itineraries:
            if isinstance(item, tuple):  # Direct flight
                flight = self.create_flight_object(item)
                dep_airport = flight.get_dep_port()
                arr_airport = flight.get_arri_port()
                price = flight.get_ticket_price()
                if dep_airport not in graph:
                    graph[dep_airport] = []
                graph[dep_airport].append((arr_airport, price, flight))
            elif isinstance(item, list):  # Itinerary
                itinerary = [self.create_flight_object(flight) for flight in item]
                dep_airport = itinerary[0].get_dep_port()
                arr_airport = itinerary[-1].get_arri_port()
                total_price = sum(float(flight.get_ticket_price()) for flight in itinerary)
                if dep_airport not in graph:
                    graph[dep_airport] = []
                graph[dep_airport].append((arr_airport, total_price, itinerary))

        priority_queue = [(0, departure_airport, [])]
        visited = {}

        while priority_queue:
            current_cost, current_airport, route = heapq.heappop(priority_queue)
            if current_airport == destination_airport:
                return route
            if current_airport in visited and current_cost >= visited[current_airport]:
                continue
            visited[current_airport] = current_cost
            for neighbor_airport, flight_price, flight_data in graph.get(current_airport, []):
                new_cost = current_cost + float(flight_price)
                new_route = route + [flight_data]
                heapq.heappush(priority_queue, (new_cost, neighbor_airport, new_route))
        return None

    def search_flights(self, date, departure, destination):
        flights_or_itineraries = self.flight_repo.find_flights(date, departure, destination)
        # Find shortest itinerary and direct flight
        shortest_itinerary = None
        shortest_itinerary_distance = float('inf')
        shortest_direct_flight = None
        shortest_direct_flight_distance = float('inf')

        for option in flights_or_itineraries:
            if isinstance(option, list):
                itinerary_flights = [self.create_flight_object(flight_tuple) for flight_tuple in option]
                total_distance = sum(flight.get_distance_km() for flight in itinerary_flights)
                if total_distance < shortest_itinerary_distance:
                    shortest_itinerary = itinerary_flights
                    shortest_itinerary_distance = total_distance
            else:
                flight_obj = self.create_flight_object(option)
                if flight_obj.get_distance_km() < shortest_direct_flight_distance:
                    shortest_direct_flight = flight_obj
                    shortest_direct_flight_distance = flight_obj.get_distance_km()

        cheapest_option = self._find_cheapest_route(flights_or_itineraries, departure, destination)

        # Return all options as a dictionary for rendering in a web template
        return {
            "shortest_itinerary": shortest_itinerary,
            "shortest_direct_flight": shortest_direct_flight,
            "cheapest_option": cheapest_option
        }

    def handle_user_choice(self, user, num_seats, choice, shortest_itinerary=None, shortest_direct_flight=None, cheapest_option=None):
        # choice: "shortest_itinerary", "shortest_direct_flight", or "cheapest_option"
        if choice == "shortest_itinerary" and shortest_itinerary:
            return self.make_reservation(user, num_seats, itinerary=shortest_itinerary)
        elif choice == "shortest_direct_flight" and shortest_direct_flight:
            return self.make_reservation(user, num_seats, direct_flight=shortest_direct_flight)
        elif choice == "cheapest_option" and cheapest_option:
            return self.make_reservation(user, num_seats, itinerary=cheapest_option)
        else:
            return {"success": False, "message": "Invalid choice or option not available."}