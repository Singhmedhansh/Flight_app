from .address import Address
class Airport:
    def __init__(self, name, code, address: Address):
        self.__code = code
        self.__name = name
        self.__address = address
        self.__flights = []

    # String representation
    def __repr__(self):
        return f"Airport(name='{self.__name}', code='{self.__code}', address={self.__address})"

    # Setters
    def set_code(self, new_code: str):
        self.__code = new_code

    def set_name(self, new_name: str):
        self.__name = new_name

    def set_address(self, new_address: Address):
        self.__address = new_address

    # Getters
    def get_name(self):
        return self.__name

    def get_code(self):
        return self.__code

    def get_address(self):
        return self.__address

    def get_flights(self):
        return self.__flights

    # Helper functions
    def add_flight(self, flight):
        self.__flights.append(flight)

    def remove_flight(self, flight):
        if flight in self.__flights:
            self.__flights.remove(flight)

    def get_flight_by_code(self, flight_code):
        for flight in self.__flights:
            if flight.get_code() == flight_code:
                return flight
        return None

    def get_total_flights(self):
        return len(self.__flights)

    def display_flights(self):
        for flight in self.__flights:
            print(flight)   # Make sure flight has a __repr__
