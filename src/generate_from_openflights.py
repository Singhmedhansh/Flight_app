import pandas as pd

# Paths to OpenFlights data files (download from https://openflights.org/data.html)

# Use dataset/ folder for input and output
AIRPORTS_CSV = 'dataset/airports.dat'
AIRLINES_CSV = 'dataset/airlines.dat'
ROUTES_CSV = 'dataset/routes.dat'

# Output files for your app
OUTPUT_AIRPORTS = 'dataset/airports.csv'
OUTPUT_AIRLINES = 'dataset/airlines.csv'
OUTPUT_FLIGHTS = 'dataset/flights.csv'

# 1. Load OpenFlights data
airports = pd.read_csv(AIRPORTS_CSV, header=None, names=[
    'AirportID', 'Name', 'City', 'Country', 'IATA', 'ICAO', 'Latitude', 'Longitude', 'Altitude', 'Timezone', 'DST', 'Tz', 'Type', 'Source'
])
airlines = pd.read_csv(AIRLINES_CSV, header=None, names=[
    'AirlineID', 'Name', 'Alias', 'IATA', 'ICAO', 'Callsign', 'Country', 'Active'
])
routes = pd.read_csv(ROUTES_CSV, header=None, names=[
    'Airline', 'AirlineID', 'SourceAirport', 'SourceAirportID', 'DestAirport', 'DestAirportID', 'Codeshare', 'Stops', 'Equipment'
])

# 2. Filter valid IATA codes (non-null, 3-letter)
airports = airports[airports['IATA'].apply(lambda x: isinstance(x, str) and len(x) == 3 and x != '\\N')]
airlines = airlines[airlines['IATA'].apply(lambda x: isinstance(x, str) and len(x) == 2 and x != '\\N')]
routes = routes[(routes['SourceAirport'].apply(lambda x: isinstance(x, str) and len(x) == 3)) &
                (routes['DestAirport'].apply(lambda x: isinstance(x, str) and len(x) == 3))]

# 3. Write airports.csv for your app
airports[['IATA', 'Name', 'City', 'Country']].rename(columns={
    'IATA': 'code', 'Name': 'name', 'City': 'city', 'Country': 'country'
}).to_csv(OUTPUT_AIRPORTS, index=False)


# Ensure major airlines are present
major_airlines = [
    {'IATA': 'EK', 'Name': 'Emirates', 'Country': 'United Arab Emirates'},
    {'IATA': 'EY', 'Name': 'Etihad Airways', 'Country': 'United Arab Emirates'},
    {'IATA': 'SQ', 'Name': 'Singapore Airlines', 'Country': 'Singapore'},
    {'IATA': 'AI', 'Name': 'Air India', 'Country': 'India'},
    {'IATA': 'BA', 'Name': 'British Airways', 'Country': 'United Kingdom'},
    {'IATA': 'NH', 'Name': 'All Nippon Airways', 'Country': 'Japan'},
    {'IATA': 'UA', 'Name': 'United Airlines', 'Country': 'United States'},
    {'IATA': 'DL', 'Name': 'Delta Air Lines', 'Country': 'United States'},
    {'IATA': 'AA', 'Name': 'American Airlines', 'Country': 'United States'},
    {'IATA': 'QF', 'Name': 'Qantas', 'Country': 'Australia'},
]

# Add missing major airlines
existing_codes = set(airlines['IATA'])
for airline in major_airlines:
    if airline['IATA'] not in existing_codes:
        airlines = pd.concat([airlines, pd.DataFrame([airline])], ignore_index=True)

airlines[['IATA', 'Name', 'Country']].rename(columns={
    'IATA': 'code', 'Name': 'name', 'Country': 'country'
}).to_csv(OUTPUT_AIRLINES, index=False)

# 5. Generate flights.csv for your app
import random
from datetime import datetime, timedelta

def random_time():
    base = datetime(2025, 10, 1)
    dep = base + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
    arr = dep + timedelta(hours=random.randint(1, 12))
    return dep.strftime('%Y-%m-%dT%H:%M'), arr.strftime('%Y-%m-%dT%H:%M')

flights = []
for _, row in routes.iterrows():
    airline_code = row['Airline']
    origin = row['SourceAirport']
    destination = row['DestAirport']
    if airline_code not in airlines['IATA'].values:
        continue
    dep_time, arri_time = random_time()
    seats_available = random.randint(50, 300)
    flights.append({
        'airline_code': airline_code,
        'origin': origin,
        'destination': destination,
        'dep_time': dep_time,
        'arri_time': arri_time,
        'seats_available': seats_available
    })


# Add famous international routes manually
famous_routes = [
    ('EK', 'DXB', 'JFK'),  # Emirates Dubai to New York
    ('EK', 'DXB', 'LAX'),  # Emirates Dubai to Los Angeles
    ('EK', 'DXB', 'SFO'),  # Emirates Dubai to San Francisco
    ('BA', 'LHR', 'JFK'),  # British Airways London to New York
    ('AI', 'DEL', 'LHR'),  # Air India Delhi to London
    ('AI', 'BOM', 'DXB'),  # Air India Mumbai to Dubai
    ('SQ', 'SIN', 'SYD'),  # Singapore Airlines Singapore to Sydney
    ('NH', 'HND', 'LAX'),  # ANA Tokyo to Los Angeles
]

# Pick a valid airline code if not present in airlines
valid_airlines = set(airlines['IATA'])
for airline_code, origin, destination in famous_routes:
    if airline_code not in valid_airlines:
        continue
    dep_time, arri_time = random_time()
    seats_available = random.randint(100, 300)
    flights.append({
        'airline_code': airline_code,
        'origin': origin,
        'destination': destination,
        'dep_time': dep_time,
        'arri_time': arri_time,
        'seats_available': seats_available
    })

flights_df = pd.DataFrame(flights)
flights_df.to_csv(OUTPUT_FLIGHTS, index=False)

print('Generated airports.csv, airlines.csv, and flights.csv!')
domestic_iata = airports[airports['Country'] == "India"]['IATA']
domestic_count = flights_df[(flights_df.origin.isin(domestic_iata)) & (flights_df.destination.isin(domestic_iata))].shape[0]
print(f'Domestic India flights: {domestic_count}')
print(f'Total flights: {flights_df.shape[0]}')
