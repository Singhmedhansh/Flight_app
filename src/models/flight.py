class Flight:
    def __init__(self, id, airline, origin, destination, departure_time, arrival_time, seats_available):
        self.id = id
        self.airline = airline
        self.origin = origin
        self.destination = destination
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.seats_available = seats_available

def __repr__(self):
    return (f"Flight(id={self.id}, airline='{self.airline}', origin='{self.origin}', "
            f"destination='{self.destination}', departure_time='{self.departure_time}', "
            f"arrival_time='{self.arrival_time}', seats_available={self.seats_available})")