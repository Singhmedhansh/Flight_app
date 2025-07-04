from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from controllers.reservation_controller import ReservationController
import json
from amadeus import Client
import csv
import os

amadeus = Client(
    client_id="TJ7cIHspFiHzdZfVAJKDFgDxTxLYOZqs",
    client_secret="tacsrVrT08fkAhAb"
)

app = Flask(__name__)
app.secret_key = 'your_secret_key'
reservation_controller = ReservationController()

def load_airline_names():
    airline_names = {}
    # Adjust path if needed
    csv_path = os.path.join(os.path.dirname(__file__), 'dataset', 'airlines.csv')
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            airline_names[row['code']] = row['name']
    return airline_names

AIRLINE_NAMES = load_airline_names()

@app.context_processor
def inject_airline_names():
    return dict(AIRLINE_NAMES=AIRLINE_NAMES)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="educative",
        password="BMWfav3$",
        database="flight"
    )

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Account WHERE username=%s", (username,))
        if cursor.fetchone():
            flash("Username already exists!")
            conn.close()
            return render_template('signup.html')
        cursor.execute("INSERT INTO Account (username, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
        conn.close()
        flash("Signup successful! Please log in.")
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM Account WHERE username=%s", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[0], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials!")
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    search_results = None
    if request.method == 'POST':
        origin = request.form['origin']
        destination = request.form['destination']
        date = request.form['date']
        try:
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=date,
                adults=1
            )
            # Improved duplicate removal: use all segments' carriers and times
            seen = set()
            filtered_results = []
            for flight in response.data:
                segments = flight['itineraries'][0]['segments']
                key = (
                    tuple(seg['carrierCode'] for seg in segments),
                    tuple(seg['departure']['at'] for seg in segments),
                    tuple(seg['arrival']['at'] for seg in segments),
                    segments[0]['departure']['iataCode'],
                    segments[-1]['arrival']['iataCode']
                )
                if key not in seen:
                    seen.add(key)
                    filtered_results.append(flight)
            search_results = filtered_results
        except Exception as e:
            flash(f"Error fetching flights: {e}")
            search_results = []
    return render_template('dashboard.html', username=username, search_results=search_results)

@app.route('/book/<int:flight_id>', methods=['POST'])
def book(flight_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    flight_data = json.loads(request.form['flight_data'])
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get user ID
    cursor.execute("SELECT account_id FROM Account WHERE username=%s", (session['username'],))
    user = cursor.fetchone()
    if not user:
        conn.close()
        flash("User not found.")
        return redirect(url_for('login'))
    user_id = user['account_id']

    # Extract flight details from Amadeus data
    flight = flight_data['itineraries'][0]['segments'][0]
    airline = flight['carrierCode']
    origin = flight['departure']['iataCode']
    destination = flight['arrival']['iataCode']
    departure_time = flight['departure']['at']
    arrival_time = flight['arrival']['at']
    seats_available = flight_data.get('numberOfBookableSeats', 1)

    # Check if flight exists
    cursor.execute("""
        SELECT flight_no FROM Flight
        WHERE airline_code=%s AND origin=%s AND destination=%s AND dep_time=%s
    """, (airline, origin, destination, departure_time))
    flight_row = cursor.fetchone()

    if flight_row:
        db_flight_id = flight_row['flight_no']
    else:
        cursor.execute("""
            INSERT INTO Flight (airline_code, origin, destination, dep_time, arri_time, seats_available)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (airline, origin, destination, departure_time, arrival_time, seats_available))
        db_flight_id = cursor.lastrowid

    # Insert reservation
    cursor.execute("""
        INSERT INTO FlightReservation (user_id, flight_no)
        VALUES (%s, %s)
    """, (user_id, db_flight_id))
    conn.commit()
    conn.close()
    flash("Flight booked successfully!")
    return redirect(url_for('dashboard'))

@app.route('/reservations')
def reservations():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT account_id FROM Account WHERE username=%s", (session['username'],))
    user = cursor.fetchone()
    if not user:
        conn.close()
        flash("User not found.")
        return redirect(url_for('login'))
    user_id = user['account_id']
    cursor.execute("""
    SELECT 
        r.creation_date,
        f.airline_code,
        f.origin,
        f.destination,
        f.dep_time,
        f.arri_time
    FROM FlightReservation r
    JOIN Flight f ON r.flight_no = f.flight_no
    WHERE r.user_id = %s
    ORDER BY r.creation_date DESC
    """, (user_id,))
    reservations = cursor.fetchall()
    conn.close()
    return render_template('reservations.html', reservations=reservations)

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('login'))

@app.route('/')
def home():
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)