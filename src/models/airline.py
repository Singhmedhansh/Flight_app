class Airline:
    def __init__(self, name, code):
        self.__name = name
        self.__code = code
        self.__flights = []  # List of flights

    # String representation
    def __repr__(self):
        return f"Airline(name='{self.__name}', code='{self.__code}', flights={len(self.__flights)})"

    # Setters
    def update_code(self, new_code: str):
        self.__code = new_code

    def update_name(self, new_name: str):
        self.__name = new_name

    # Getters
    def get_name(self):
        return self.__name

    def get_code(self):
        return self.__code

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
            print(flight)

    # # String representation
    # def __repr__(self):
    #     return f"Airline(name='{self.__name}', code='{self.__code}', flights={len(self.__flights)})"

# class Aircraft:
#   def __init__(self, name, code, model, seatCapacity, seats):
#     self.__name = name
#     self.__code = code
#     self.__models = model
#     self.__seatCapacity = seatCapacity
#     self.__seats = [] # List of seats

# The Airline is a singleton class that ensures it will have only one active instance at a time
# class __Airline(object):
#   __instances = None
  
#   def __new__(cls):
#     if cls.__instances is None:
#         cls.__instances = super(__Airline, cls).__new__(cls)
#     return cls.__instances

# class Airline(metaclass = __Airline):
#   def __init__(self, name, code):
#     self.__name = name
#     self.__code = code # IATA_CODE
#     self.__flights = [] # List of flights
#     # self.__aircrafts = [] # List of aircrafts
#     # self.__crew = [] # List of crew