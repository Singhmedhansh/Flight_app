
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from controllers.reservation_controller import ReservationController
from controllers.flight_controller import FlightController
import json
import csv
import os
from datetime import datetime
from airport_utils import load_airport_cities
from amadeus import Client

amadeus = Client(
    client_id='TJ7cIHspFiHzdZfVAJKDFgDxTxLYOZqs',
    client_secret='tacsrVrT08fkAhAb'
)

import csv

CITY_TO_AIRPORT = {}
# Ensure we open the CSV relative to this file, not the current working directory
CSV_PATH = os.path.join(os.path.dirname(__file__), 'airports.csv')
if not os.path.exists(CSV_PATH):
    # fallback to dataset/airports.csv if present
    CSV_PATH = os.path.join(os.path.dirname(__file__), 'dataset', 'airports.csv')

with open(CSV_PATH, encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        city = row.get('municipality', '') or row.get('city', '')
        code = row.get('iata_code', '').strip().upper()
        if city and code and len(code) == 3:
            city_key = city.strip().lower()
            CITY_TO_AIRPORT.setdefault(city_key, []).append(code)
            CITY_TO_AIRPORT.setdefault(code.lower(), []).append(code)
# Remove duplicates
for k in CITY_TO_AIRPORT:
    CITY_TO_AIRPORT[k] = list(set(CITY_TO_AIRPORT[k]))
print(f"Loaded {len(CITY_TO_AIRPORT)} city/airport mappings.")

app = Flask(__name__)
app.secret_key = 'your_secret_key'
reservation_controller = ReservationController()
flight_controller = FlightController()

# Custom Jinja2 filters for datetime formatting
@app.template_filter('format_datetime')
def format_datetime_filter(value, format='%H:%M'):
    """Format datetime object or ISO string to time format"""
    if isinstance(value, str):
        # Parse ISO 8601 format: 2026-03-15T14:30:00+00:00
        if 'T' in value:
            value = value.split('T')[1].split('+')[0].split('.')[0]  # Extract time
            return value[:5]  # Return HH:MM
        return value
    elif hasattr(value, 'strftime'):
        return value.strftime(format)
    return str(value)

@app.template_filter('format_date')
def format_date_filter(value, format='%d %b %Y'):
    """Format datetime object or ISO string to date format"""
    if isinstance(value, str):
        # Parse ISO 8601 format: 2026-03-15T14:30:00+00:00
        if 'T' in value:
            date_str = value.split('T')[0]  # Extract date
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.strftime(format)
            except:
                return date_str
        return value
    elif hasattr(value, 'strftime'):
        return value.strftime(format)
    return str(value)
 
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join('static', 'profile_pics')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Account WHERE username=%s", (session['username'],))
    user = cursor.fetchone()
    if not user:
        conn.close()
        flash("User not found.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_username = request.form['username']
        new_email = request.form['email']
        new_password = request.form['password']
        profile_pic_url = user.get('profile_pic_url', '')

        # Handle profile picture upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{session['username']}_{file.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(file_path)
                profile_pic_url = '/' + file_path.replace('\\', '/')

        if new_password:
            hashed_password = generate_password_hash(new_password)
            cursor.execute(
                "UPDATE Account SET username=%s, email=%s, password=%s, profile_pic_url=%s WHERE account_id=%s",
                (new_username, new_email, hashed_password, profile_pic_url, user['account_id'])
            )
        else:
            cursor.execute(
                "UPDATE Account SET username=%s, email=%s, profile_pic_url=%s WHERE account_id=%s",
                (new_username, new_email, profile_pic_url, user['account_id'])
            )
        conn.commit()
        session['username'] = new_username
        flash("Profile updated successfully.")
        cursor.execute("SELECT * FROM Account WHERE username=%s", (new_username,))
        user = cursor.fetchone()
    conn.close()
    return render_template('profile.html', user=user)


# Cancel reservation route (POST only, AJAX/JSON)
@app.route('/cancel_reservation', methods=['POST'])
def cancel_reservation():
    if 'username' not in session:
        flash('Not logged in.')
        return redirect(url_for('login'))
    reservation_id = request.form.get('reservation_id')
    if not reservation_id:
        flash('Reservation ID missing.')
        return redirect(url_for('reservations'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM FlightReservation WHERE id = %s", (reservation_id,))
        conn.commit()
        deleted = cursor.rowcount
        conn.close()
        if deleted:
            flash('Reservation canceled successfully.')
        else:
            flash('Reservation not found.')
    except Exception as e:
        flash(f'Error: {str(e)}')
    return redirect(url_for('reservations'))


def load_airline_names():
    airline_names = {}
    # Adjust path if needed
    csv_path = os.path.join(os.path.dirname(__file__), 'dataset', 'airlines.csv')
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            airline_names[row['code']] = row['name']
    return airline_names

# Helper function to generate mock seat data
def generate_mock_seats(rows, columns):
    """Generate mock seat data for fallback"""
    import random
    seats = []
    letters = ['A', 'B', 'C', 'D', 'E', 'F'][:columns]
    blocked_seats = random.sample(range(rows * columns), k=rows * columns // 4)  # 25% occupied
    
    idx = 0
    for row in range(1, rows + 1):
        for col, letter in enumerate(letters):
            is_blocked = idx in blocked_seats
            seats.append({
                'number': f"{row}{letter}",
                'travelerPricing': [{
                    'seatAvailabilityStatus': 'BLOCKED' if is_blocked else 'AVAILABLE'
                }],
                'coordinates': {
                    'x': col,
                    'y': row
                }
            })
            idx += 1
    return seats

AIRLINE_NAMES = load_airline_names()
AIRPORT_CITIES = load_airport_cities()


@app.context_processor
def inject_names():
    return dict(AIRLINE_NAMES=AIRLINE_NAMES, AIRPORT_CITIES=AIRPORT_CITIES)

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

    # Fetch user info including profile_pic_url
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Account WHERE username=%s", (username,))
    user = cursor.fetchone()

    # Fetch reservations for the user
    cursor.execute("""
        SELECT f.origin, f.destination, f.dep_time
        FROM FlightReservation r
        JOIN Flight f ON r.flight_id = f.id
        JOIN Account a ON r.user_id = a.account_id
        WHERE a.username = %s
        ORDER BY f.dep_time ASC
        LIMIT 3
    """, (username,))
    reservations = cursor.fetchall()

    search_results = None
    cheapest_flight = None

    if request.method == 'POST':
        origin_input = request.form['origin'].strip().lower()
        destination_input = request.form['destination'].strip().lower()
        date = request.form['date']
        
        # Get filter parameters
        max_price = request.args.get('maxPrice', type=float)
        max_stops = request.args.get('maxStops', type=int)
        included_airlines = request.args.getlist('airlines')

        origin_codes = CITY_TO_AIRPORT.get(origin_input)
        destination_codes = CITY_TO_AIRPORT.get(destination_input)

        origin = origin_codes[0] if origin_codes else (origin_input.upper() if len(origin_input) == 3 else '')
        destination = destination_codes[0] if destination_codes else (destination_input.upper() if len(destination_input) == 3 else '')

        print(f"Origin: {origin} | Destination: {destination} | Date: {date}")

        if not origin or len(origin) != 3:
            flash("Unknown origin city or airport.")
            return redirect(url_for('dashboard'))
        if not destination or len(destination) != 3:
            flash("Unknown destination city or airport.")
            return redirect(url_for('dashboard'))
        try:
            # Try Amadeus first (if configured)
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=date,
                adults=1,
                max=50  # Get more results for comparison
            )
            print(response.data)
            seen = set()
            filtered_results = []
            all_prices = []
            
            for flight in response.data:
                segments = flight['itineraries'][0]['segments']
                
                # Apply filters
                try:
                    price = float(flight.get('price', {}).get('total', 0))
                    all_prices.append((price, flight))
                    
                    # Price filter
                    if max_price and price > max_price:
                        continue
                    
                    # Stops filter
                    num_stops = len(segments) - 1
                    if max_stops is not None and num_stops > max_stops:
                        continue
                    
                    # Airline filter
                    airline_code = segments[0]['carrierCode']
                    if included_airlines and airline_code not in included_airlines:
                        continue
                    
                except (KeyError, ValueError):
                    pass
                
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
            
            # Find cheapest alternative
            if all_prices:
                all_prices.sort(key=lambda x: x[0])
                cheapest_flight = all_prices[0][1]
            
            for flight in filtered_results:
                for seg in flight['itineraries'][0]['segments']:
                    seg['departure']['city'] = AIRPORT_CITIES.get(seg['departure']['iataCode'], seg['departure']['iataCode'])
                    seg['arrival']['city'] = AIRPORT_CITIES.get(seg['arrival']['iataCode'], seg['arrival']['iataCode'])
            search_results = filtered_results
        except Exception as e:
            # If Amadeus is not configured or fails, fall back to the local DB flights table
            import traceback
            print("Amadeus search failed, falling back to DB search:")
            print(traceback.format_exc())
            try:
                conn2 = get_db_connection()
                cur = conn2.cursor(dictionary=True)
                # Attempt to read columns that exist in DB (common names used elsewhere in the project)
                cur.execute("SELECT id, airline_code, origin, destination, dep_time, arri_time, seats_available FROM Flight WHERE origin=%s AND destination=%s", (origin, destination))
                rows = cur.fetchall()
                conn2.close()
                db_results = []
                for row in rows:
                    seg = {
                        'carrierCode': row.get('airline_code') or row.get('airline') or 'UNK',
                        'numberOfBookableSeats': row.get('seats_available', 1),
                        'departure': {
                            'at': row.get('dep_time') or row.get('departure_time') or '',
                            'iataCode': row.get('origin')
                        },
                        'arrival': {
                            'at': row.get('arri_time') or row.get('arrival_time') or '',
                            'iataCode': row.get('destination')
                        }
                    }
                    flight_offer = {'itineraries': [{'segments': [seg]}]}
                    # add readable city names
                    for seg in flight_offer['itineraries'][0]['segments']:
                        seg['departure']['city'] = AIRPORT_CITIES.get(seg['departure']['iataCode'], seg['departure']['iataCode'])
                        seg['arrival']['city'] = AIRPORT_CITIES.get(seg['arrival']['iataCode'], seg['arrival']['iataCode'])
                    db_results.append(flight_offer)
                search_results = db_results
                if not search_results:
                    flash(f"No flights found in DB from {origin} to {destination}.")
            except Exception as db_e:
                print("DB fallback search failed:", db_e)
                flash(f"Error fetching flights: {e}")
                search_results = []

    conn.close()
    
    # Get unique airlines for filter
    unique_airlines = set()
    if search_results:
        for flight in search_results:
            airline_code = flight['itineraries'][0]['segments'][0]['carrierCode']
            unique_airlines.add(airline_code)
    
    return render_template(
        'dashboard.html',
        username=username,
        reservations=reservations,
        search_results=search_results,
        cheapest_flight=cheapest_flight,
        unique_airlines=sorted(unique_airlines),
        AIRLINE_NAMES=AIRLINE_NAMES,
        user=user  # Pass user to template for profile picture
    )

# Step 1: Book button goes to seat selection page
@app.route('/booking', methods=['POST'])
def booking():
    """Display seat selection page after user clicks View Deals"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get flight data from form
    flight_data = json.loads(request.form['flight_data'])
    
    # Store flight data in session for later use
    session['current_flight_offer'] = flight_data
    session.modified = True
    
    # Extract flight details
    segments = flight_data['itineraries'][0]['segments']
    first_segment = segments[0]
    airline_name = AIRLINE_NAMES.get(first_segment['carrierCode'], first_segment['carrierCode'])
    
    # Add city names for display
    first_segment['departure']['city'] = AIRPORT_CITIES.get(first_segment['departure']['iataCode'], first_segment['departure']['iataCode'])
    first_segment['arrival']['city'] = AIRPORT_CITIES.get(first_segment['arrival']['iataCode'], first_segment['arrival']['iataCode'])
    
    return render_template('booking.html', 
                         flight=first_segment, 
                         airline_name=airline_name,
                         flight_data=flight_data)



def generate_booking_reference():
    """Generate a unique booking reference (e.g., ABC1234567)"""
    import string
    import random
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=10))


@app.route('/confirm', methods=['POST'])
def confirm():
    """Display confirmation page with flight summary and seat"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    selected_seat = request.form.get('seat_number')
    flight_data = session.get('current_flight_offer')
    
    if not flight_data or not selected_seat:
        flash('Session expired. Please search for flights again.', 'error')
        return redirect(url_for('dashboard'))
    
    # Store selected seat in session
    session['selected_seat'] = selected_seat
    session.modified = True
    
    # Extract flight details
    segments = flight_data['itineraries'][0]['segments']
    first_segment = segments[0]
    last_segment = segments[-1]
    
    airline_name = AIRLINE_NAMES.get(first_segment['carrierCode'], first_segment['carrierCode'])
    
    # Prepare flight info for confirmation page
    flight_info = {
        'airline_name': airline_name,
        'airline_code': first_segment['carrierCode'],
        'flight_number': f"{first_segment['carrierCode']}{first_segment.get('number', '')}",
        'origin': first_segment['departure']['iataCode'],
        'destination': last_segment['arrival']['iataCode'],
        'origin_city': AIRPORT_CITIES.get(first_segment['departure']['iataCode'], first_segment['departure']['iataCode']),
        'dest_city': AIRPORT_CITIES.get(last_segment['arrival']['iataCode'], last_segment['arrival']['iataCode']),
        'dep_time': first_segment['departure']['at'],
        'arr_time': last_segment['arrival']['at'],
        'stops': max(len(segments) - 1, 0),
        'duration': flight_data.get('itineraries', [{}])[0].get('duration', 'Duration N/A'),
        'price': flight_data.get('price', {}).get('total', 'N/A'),
        'seat_number': selected_seat
    }
    
    return render_template('confirm.html', flight=flight_info)


@app.route('/process-booking', methods=['POST'])
def process_booking():
    """Create reservation and redirect to ticket"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    flight_data = session.get('current_flight_offer')
    selected_seat = session.get('selected_seat')
    
    if not flight_data or not selected_seat:
        flash('Session expired. Please search for flights again.', 'error')
        return redirect(url_for('dashboard'))
    
    # Extract flight details and create reservation
    segments = flight_data['itineraries'][0]['segments']
    first_segment = segments[0]
    last_segment = segments[-1]
    
    # Generate unique booking reference
    booking_ref = generate_booking_reference()
    
    reservation = {
        'booking_reference': booking_ref,
        'airline_name': AIRLINE_NAMES.get(first_segment['carrierCode'], first_segment['carrierCode']),
        'airline_code': first_segment['carrierCode'],
        'flight_number': f"{first_segment['carrierCode']}{first_segment.get('number', '')}",
        'origin': first_segment['departure']['iataCode'],
        'destination': last_segment['arrival']['iataCode'],
        'origin_city': AIRPORT_CITIES.get(first_segment['departure']['iataCode'], first_segment['departure']['iataCode']),
        'dest_city': AIRPORT_CITIES.get(last_segment['arrival']['iataCode'], last_segment['arrival']['iataCode']),
        'dep_time': first_segment['departure']['at'],
        'arr_time': last_segment['arrival']['at'],
        'stops': max(len(segments) - 1, 0),
        'duration': flight_data.get('itineraries', [{}])[0].get('duration', 'Duration N/A'),
        'price': flight_data.get('price', {}).get('total', 'N/A'),
        'seat_number': selected_seat
    }
    
    # Add to session reservations
    reservations = session.get('reservations', [])
    reservations.append(reservation)
    session['reservations'] = reservations
    
    # Store current booking for ticket display
    session['current_booking'] = reservation
    
    # Clear temporary flight data
    session.pop('current_flight_offer', None)
    session.pop('selected_seat', None)
    session.modified = True
    
    return redirect(url_for('ticket'))


@app.route('/ticket')
def ticket():
    """Display digital ticket for the booking"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    booking = session.get('current_booking')
    if not booking:
        flash('No booking found. Please book a flight first.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('ticket.html', booking=booking)


# Get SeatMap from Amadeus API
@app.route('/api/seatmap', methods=['POST'])
def get_seatmap():
    if 'username' not in session:
        return {'error': 'Unauthorized'}, 401
    
    try:
        flight_offer_id = request.json.get('flightOfferId')
        
        # Call Amadeus SeatMap API
        response = amadeus.shopping.seatmaps.post(
            json.dumps({'data': [{'type': 'flight-offer', 'id': flight_offer_id}]})
        )
        
        return {'data': response.data}
    except Exception as e:
        print(f"SeatMap API error: {e}")
        # Return mock seatmap data as fallback
        return {
            'data': [{
                'decks': [{
                    'deckConfiguration': {
                        'width': 6,
                        'length': 30
                    },
                    'seats': generate_mock_seats(30, 6)
                }]
            }]
        }
# Note: The /confirm_booking route with database persistence has been replaced with
# session-based persistence above. Database integration can be added later if needed.

def generate_booking_reference():
    """Generate a random booking reference code"""
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/reservations')
def reservations():
    if 'username' not in session:
        flash("Please log in to view your reservations.", "error")
        return redirect(url_for('login'))

    reservations = session.get('reservations', [])
    return render_template('reservations.html', reservations=reservations)

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('login'))

@app.route('/')
def home():
    return redirect(url_for('login'))

# New component routes
@app.route('/seat-selector')
def seat_selector():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('seat_selector.html')

@app.route('/price-prediction')
def price_prediction():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('components/price_prediction.html')

@app.route('/booking-progress')
def booking_progress():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('components/booking_progress.html')

if __name__ == '__main__':
    app.run(debug=True)