# Import necessary libraries
# import the connector
import mysql.connector
import pandas as pd
from sqlalchemy import create_engine

# establish a connection to MySQL database
connection = mysql.connector.connect(
  host="localhost",
  user="educative",
  password="BMWfav3$",
  database="flight"
)

# create a cusrsor object to perform quries
mycursor = connection.cursor()



## Clear tables before seeding to avoid duplicates
mycursor.execute("DELETE FROM flight;")
mycursor.execute("DELETE FROM airport;")
mycursor.execute("DELETE FROM airline;")
connection.commit()

# Step 1: Insert airlines
airlines_df = pd.read_csv('../dataset/airlines.csv')
for _, row in airlines_df.iterrows():
    mycursor.execute("""
        INSERT IGNORE INTO airline (code, name, country)
        VALUES (%s, %s, %s)
    """, (row['code'], row['name'], row['country']))
connection.commit()



################################################################################################################


# Step 2: Insert airports (no address table, just code, name, city, country)
airports_df = pd.read_csv('../dataset/airports.csv')
for _, row in airports_df.iterrows():
    mycursor.execute("""
        INSERT IGNORE INTO airport (code, name, city, country)
        VALUES (%s, %s, %s, %s)
    """, (row['code'], row['name'], row['city'], row['country']))
connection.commit()




################################################################################################################


# Step 3: Insert flights
flights_df = pd.read_csv('../dataset/flights.csv')
insert_flight_query = """
    INSERT IGNORE INTO flight (airline_code, origin, destination, dep_time, arri_time, seats_available)
    VALUES (%s, %s, %s, %s, %s, %s)
"""
relevant_columns = ['airline_code', 'origin', 'destination', 'dep_time', 'arri_time', 'seats_available']
flight_data = [tuple(row) for row in flights_df[relevant_columns].values]
batch_size = 1000
for i in range(0, len(flight_data), batch_size):
    batch = flight_data[i:i+batch_size]
    mycursor.executemany(insert_flight_query, batch)
    connection.commit()
print(f"{len(flight_data)} flights inserted into the database.")


################################################################################################################
# Create an Admin
# Create a cursor object
mycursor = connection.cursor()

# Insert roles (ignore duplicates)
mycursor.execute("INSERT IGNORE INTO Role(name) VALUES ('admin');")
mycursor.execute("INSERT IGNORE INTO Role(name) VALUES ('user');")

# Insert admin account (ignore duplicate)
mycursor.execute("INSERT IGNORE INTO account(username, password, status) VALUES ('admin_user', '12345', 'active');")

# Fetch the account_id of the newly inserted admin account
mycursor.execute("SELECT account_id FROM Account WHERE username = 'admin_user';")
admin_account_id = mycursor.fetchone()[0]

# Fetch the role_id of the admin role
mycursor.execute("SELECT role_id FROM Role WHERE name = 'admin';")
admin_role_id = mycursor.fetchone()[0]

# Insert into Account_Role (assign admin role to admin_user, ignore duplicates)
mycursor.execute("INSERT IGNORE INTO account_Role(account_id, role_id) VALUES (%s, %s);", (admin_account_id, admin_role_id))

# Commit the changes
connection.commit()

mycursor.close()
connection.close()