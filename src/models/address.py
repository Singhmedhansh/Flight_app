class Address:
    def __init__(self, city, state, country): 
        self.__city = city
        self.__state = state
        self.__country = country

    # String representation
    def __repr__(self):
        return f"city='{self.__city}', state='{self.__state}', country='{self.__country}'"

    # Getters
    def get_city(self):
        return self.__city

    def get_state(self):
        return self.__state

    def get_country(self):
        return self.__country

    # Setters
    def update_city(self, new_city: str):
        self.__city = new_city

    def update_state(self, new_state: str):
        self.__state = new_state

    def update_country(self, new_country: str):
        self.__country = new_country
