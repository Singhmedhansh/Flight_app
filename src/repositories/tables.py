import mysql.connector

# establish a connection to MySQL database
connection = mysql.connector.connect(
  host="localhost",
  user="educative",
  password="BMWfav3$",
  database="flight"
)

# create a cursor object to perform queries
mycursor = connection.cursor()

# Drop tables if they already exist (to start fresh)
tables = [
    'Itinerary_Passenger', 'Passenger', 'Itinerary_Reservation', 'Itinerary',
    'FlightReservation', 'Flight', 'Account_Role', 'Role', 'Account',
    'Airport', 'Airline', 'Address', 'Payment', 'Admin', 'Customer'
]
for table in tables:
    mycursor.execute(f"DROP TABLE IF EXISTS {table}")

# Create Address table
mycursor.execute("""
CREATE TABLE Address (
    address_id INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(255),
    state VARCHAR(255),
    country VARCHAR(255)
)
""")

# Create Airline table
mycursor.execute("""
CREATE TABLE Airline (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255)
)
""")

# Create Airport table
mycursor.execute("""
CREATE TABLE Airport (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255),
    address_id INT,
    FOREIGN KEY (address_id) REFERENCES Address(address_id)
)
""")

# Create Role table
mycursor.execute("""
CREATE TABLE Role (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50)
)
""")

# Create Account table
mycursor.execute("""
CREATE TABLE Account (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE,
    password VARCHAR(255),
    status VARCHAR(50)
)
""")

# Create Account_Role table for many-to-many relationship between Account and Role
mycursor.execute("""
CREATE TABLE Account_Role (
    account_id INT,
    role_id INT,
    PRIMARY KEY (account_id, role_id),
    FOREIGN KEY (account_id) REFERENCES Account(account_id),
    FOREIGN KEY (role_id) REFERENCES Role(role_id)
)
""")

# Create Flight table
mycursor.execute("""
CREATE TABLE Flight (
    flight_no INT AUTO_INCREMENT PRIMARY KEY,
    airline_code VARCHAR(10),
    distance_km DECIMAL(10, 2),
    dep_time DATETIME,
    arri_time DATETIME,
    dep_port VARCHAR(10),
    arri_port VARCHAR(10),
    booked_seats INT DEFAULT 0,
    FOREIGN KEY (airline_code) REFERENCES Airline(code),
    FOREIGN KEY (dep_port) REFERENCES Airport(code),
    FOREIGN KEY (arri_port) REFERENCES Airport(code)
)
""")

# Create FlightReservation table
mycursor.execute("""
CREATE TABLE FlightReservation (
    reservation_number INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    flight_no INT,
    seats INT,
    creation_date DATETIME,
    payment_amount DECIMAL (10, 2),
    FOREIGN KEY (user_id) REFERENCES Account(account_id),
    FOREIGN KEY (flight_no) REFERENCES Flight(flight_no)
)
""")

# Create Payment table
mycursor.execute("""
CREATE TABLE Payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    amount DECIMAL(10, 2),
    payment_method VARCHAR(50),
    status VARCHAR(50),
    payment_date DATETIME
)
""")

# Create Itinerary table
mycursor.execute("""
CREATE TABLE Itinerary (
    itinerary_id INT AUTO_INCREMENT PRIMARY KEY,
    starting_airport VARCHAR(10),
    final_airport VARCHAR(10),
    creation_date DATETIME,
    FOREIGN KEY (starting_airport) REFERENCES Airport(code),
    FOREIGN KEY (final_airport) REFERENCES Airport(code)
)
""")

# Create Itinerary_Reservation table for many-to-many relationship between Itinerary and FlightReservation
mycursor.execute("""
CREATE TABLE Itinerary_Reservation (
    itinerary_id INT,
    reservation_number INT,
    PRIMARY KEY (itinerary_id, reservation_number),
    FOREIGN KEY (itinerary_id) REFERENCES Itinerary(itinerary_id),
    FOREIGN KEY (reservation_number) REFERENCES FlightReservation(reservation_number)
)
""")

# Create Passenger table
mycursor.execute("""
CREATE TABLE Passenger (
    passenger_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT,
    name VARCHAR(255),
    passport_number VARCHAR(50),
    passport_issue DATE,
    passport_expiry DATE,
    FOREIGN KEY (account_id) REFERENCES Account(account_id)
)
""")

# Create Itinerary_Passenger table for many-to-many relationship between Itinerary and Passenger
mycursor.execute("""
CREATE TABLE Itinerary_Passenger (
    itinerary_id INT,
    passenger_id INT,
    PRIMARY KEY (itinerary_id, passenger_id),
    FOREIGN KEY (itinerary_id) REFERENCES Itinerary(itinerary_id),
    FOREIGN KEY (passenger_id) REFERENCES Passenger(passenger_id)
)
""")

# Create Admin table (inherits Account)
mycursor.execute("""
CREATE TABLE Admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT,
    FOREIGN KEY (account_id) REFERENCES Account(account_id)
)
""")

# Create Customer table (inherits Account)
mycursor.execute("""
CREATE TABLE Customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT,
    address_id INT,
    FOREIGN KEY (account_id) REFERENCES Account(account_id),
    FOREIGN KEY (address_id) REFERENCES Address(address_id)
)
""")

# Commit the changes
connection.commit()

# Close the cursor and connection
mycursor.close()
connection.close()

print("All tables created successfully!")