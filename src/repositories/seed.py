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


# Step 1: Create a DataFrame with the data
df = pd.read_csv('C:/Users/singh/Downloads/Flight_res/dataset/airlines.csv')  

# Step 2: Create a SQLAlchemy engine to connect to the MySQL database
engine = create_engine("mysql+mysqlconnector://educative:BMWfav3$@localhost/flight")

# Step 3: Convert the Pandas DataFrame to a format for MySQL table insertion
df.to_sql('airline', con=engine, if_exists='append', index=False)

connection.commit()

#print(mycursor.rowcount, "record inserted.")
#mycursor.execute("Select * from Airline")



################################################################################################################

# Load the dataframe from the CSV file
df = pd.read_csv('C:/Users/singh/Downloads/Flight_res/dataset/airports.csv')

mycursor = connection.cursor()

# Function to insert into the Address table and get address_id
def insert_address(city, state, country):
    mycursor.execute("""
        INSERT INTO address (city, state, country)
        VALUES (%s, %s, %s)
    """, (city, state, country))
    
    connection.commit()  # Save the changes
    return mycursor.lastrowid  # Get the last inserted address_id

# Iterate over each row in the dataframe
for index, row in df.iterrows():
    # Extract city, state, country
    city = row['city']
    state = row['state']
    country = row['country']

    # Insert into Address and get address_id
    address_id = insert_address(city, state, country)

    # Insert into Airport using the code, name, and address_id
    mycursor.execute("""
        INSERT INTO airport (code, name, address_id)
        VALUES (%s, %s, %s)
    """, (row['code'], row['name'], address_id))
    
    connection.commit()  # Save the changes




################################################################################################################

# Load the dataframe from the CSV file
flights_df = pd.read_csv('C:/Users/singh/Downloads/Flight_res/dataset/flights.csv')
print(flights_df.columns)
# Create a cursor object
mycursor = connection.cursor()

# Prepare an SQL query to insert data into the Flight table
# flight_no
insert_flight_query = """
    INSERT INTO flight (airline_code, distance_km, dep_time, arri_time, dep_port, arri_port, booked_seats)
    VALUES (%s, %s, %s, %s, %s, %s, 0)
"""

# Select only the relevant columns
relevant_columns = ['airline_code', 'distance_km', 'dep_time', 'arri_time', 'dep_port', 'arri_port']
# Convert the selected columns to tuples (rows of data)
flight_data = [tuple(row) for row in flights_df[relevant_columns].values]

# Execute the insert query for each row of flight data
batch_size = 1000  # Adjust the batch size as needed

for i in range(0, len(flight_data), batch_size):
    batch = flight_data[i:i+batch_size]
    mycursor.executemany(insert_flight_query, batch)
    connection.commit()  # Commit after each batch to save the changes

print(f"{len(flight_data)} flights inserted into the database.")


################################################################################################################
# Create an Admin
# Create a cursor object
mycursor = connection.cursor()

# Insert roles
mycursor.execute("INSERT INTO Role(name) VALUES ('admin');")
mycursor.execute("INSERT INTO Role(name) VALUES ('user');")

# Insert admin account
mycursor.execute("INSERT INTO account(username, password, status) VALUES ('admin_user', '12345', 'active');")

# Fetch the account_id of the newly inserted admin account
mycursor.execute("SELECT account_id FROM Account WHERE username = 'admin_user';")
admin_account_id = mycursor.fetchone()[0]

# Fetch the role_id of the admin role
mycursor.execute("SELECT role_id FROM Role WHERE name = 'admin';")
admin_role_id = mycursor.fetchone()[0]

# Insert into Account_Role (assign admin role to admin_user)
mycursor.execute("INSERT INTO account_Role(account_id, role_id) VALUES (%s, %s);", (admin_account_id, admin_role_id))

# Commit the changes
connection.commit()

mycursor.close()
connection.close()