from flask import Flask, render_template, request, redirect, url_for, session, flash
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except Exception:
    mysql = None
    MYSQL_AVAILABLE = False
from werkzeug.security import generate_password_hash, check_password_hash
from controllers.reservation_controller import ReservationController
import json
try:
    from amadeus import Client
    AMADEUS_AVAILABLE = True
except Exception:
    Client = None
    AMADEUS_AVAILABLE = False
import csv
import os
from urllib.parse import unquote
from werkzeug.utils import secure_filename
from datetime import datetime


def fetch_user_reservations(username, limit=5):
    """Return a list of recent reservations for the given username.

    Each reservation is a dict with parsed datetime objects when possible.
    """
    conn = get_db_connection()
    cursor, _ = make_cursor(conn)
    try:
        execute_with_fallback(cursor, conn, "SELECT account_id FROM Account WHERE username=%s", (username,))
        user = cursor.fetchone()
    except Exception:
        execute_with_fallback(cursor, conn, "SELECT account_id FROM Account WHERE username=?", (username,))
        user = cursor.fetchone()
    if not user:
        conn.close()
        return []
    # account id may be dict-like or row-like
    try:
        user_id = user['account_id']
    except Exception:
        try:
            user_id = user[0]
        except Exception:
            conn.close()
            return []

    # Fetch reservations from FlightReservation table first to avoid JOIN issues
    # which can vary between sqlite/mysql schemas. We'll then fetch flight details
    # per reservation in a separate query.
    q_res = "SELECT * FROM FlightReservation WHERE user_id = %s ORDER BY creation_date DESC LIMIT %s"
    execute_with_fallback(cursor, conn, q_res, (user_id, limit))
    res_rows = cursor.fetchall()

    def _parse_dt(v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            s = v.strip()
            if s.endswith('Z'):
                s = s[:-1]
            for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(s, fmt)
                except Exception:
                    continue
        return v

    out = []
    for row in res_rows:
        # support dict-like rows or sequences
        try:
            reservation_id = row.get('id') or row.get('reservation_number') or row.get('reservation_id')
        except Exception:
            # tuple/sequence fallback: try common positions
            try:
                reservation_id = row[0]
            except Exception:
                reservation_id = None

        try:
            flight_no = row.get('flight_no')
        except Exception:
            try:
                # tuple fallback: flight_no often at position 2
                flight_no = row[2]
            except Exception:
                flight_no = None

        try:
            creation_date = row.get('creation_date')
        except Exception:
            try:
                creation_date = row[3]
            except Exception:
                creation_date = None

        airline_code = None; dep_port = None; arri_port = None; dep_time = None; arri_time = None
        if flight_no:
            # fetch flight details
            try:
                execute_with_fallback(cursor, conn, "SELECT airline_code, dep_port, arri_port, dep_time, arri_time FROM Flight WHERE flight_no = %s", (flight_no,))
                frow = cursor.fetchone()
                try:
                    airline_code = frow['airline_code']
                    dep_port = frow['dep_port']
                    arri_port = frow['arri_port']
                    dep_time = frow['dep_time']
                    arri_time = frow['arri_time']
                except Exception:
                    # tuple fallback
                    try:
                        airline_code = frow[0]
                        dep_port = frow[1]
                        arri_port = frow[2]
                        dep_time = frow[3]
                        arri_time = frow[4]
                    except Exception:
                        pass
            except Exception:
                # ignore flight lookup failures and continue
                pass

        out.append({
            'id': reservation_id,
            'flight_no': flight_no,
            'airline_code': airline_code,
            'dep_port': dep_port,
            'arri_port': arri_port,
            'dep_time': _parse_dt(dep_time),
            'arri_time': _parse_dt(arri_time),
            'creation_date': _parse_dt(creation_date),
        })

    conn.close()
    return out

if AMADEUS_AVAILABLE and Client is not None:
    try:
        amadeus = Client(
            client_id="TJ7cIHspFiHzdZfVAJKDFgDxTxLYOZqs",
            client_secret="tacsrVrT08fkAhAb"
        )
    except Exception:
        amadeus = None
        AMADEUS_AVAILABLE = False
else:
    amadeus = None

app = Flask(__name__)
app.secret_key = 'your_secret_key'
reservation_controller = ReservationController()

# Upload configuration for profile photos
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_airline_names():
    airline_names = {}
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

from config.database_config import get_db_connection  # type: ignore


def make_cursor(conn):
    """Return a cursor for the given connection.

    Tries to request a dictionary-style cursor (MySQL connector). If the
    connection/cursor implementation doesn't accept that keyword (sqlite3),
    fall back to the default cursor. Returns a tuple (cursor, dict_rows)
    where dict_rows is True when the cursor will return dict-like rows.
    """
    try:
        cur = conn.cursor(dictionary=True)
        return cur, True
    except TypeError:
        # sqlite3's cursor() doesn't accept dictionary=True
        cur = conn.cursor()
        return cur, False


def execute_with_fallback(cursor, conn, query, params=None):
    """Execute a query trying MySQL-style %s placeholders first, then
    falling back to sqlite3-style ? placeholders if the first attempt fails.

    Returns whatever cursor.execute returns.
    """
    # Normalize params: if a single iterable (tuple/list) was passed as the sole element,
    # expand it so cursor.execute receives the correct sequence. This avoids issues where
    # callers accidentally pass a nested tuple like ((a,b),) which causes MySQL to report
    # 'Not all parameters were used'.
    _params = params
    if params is not None:
        try:
            # If params is a sequence-like with exactly one element which itself is a
            # sequence, unwrap it.
            if isinstance(params, (list, tuple)) and len(params) == 1 and isinstance(params[0], (list, tuple)):
                _params = params[0]
        except Exception:
            _params = params

    try:
        if _params is None:
            return cursor.execute(query)
        return cursor.execute(query, _params)
    except Exception as e:
        # If the database is sqlite, try replacing %s with ? placeholder and retry.
        try:
            alt_query = query.replace('%s', '?')
            if _params is None:
                return cursor.execute(alt_query)
            return cursor.execute(alt_query, _params)
        except Exception:
            # Provide a clearer error message including the query and params to help
            # identify mismatch problems when debugging.
            raise RuntimeError(f"Query execution failed. Query: {query!r}, params: {_params!r}, original error: {e}") from e


@app.context_processor
def inject_user_profile():
    """Inject profile_url into templates when user is logged in."""
    profile_url = None
    username = session.get('username')
    if username:
        # look for uploaded profile file
        for ext in ('.png', '.jpg', '.jpeg', '.gif', '.heic', '.heif'):
            fname = f"{username}_profile{ext}"
            file_path = os.path.join(UPLOAD_FOLDER, fname)
            if os.path.exists(file_path):
                profile_url = url_for('static', filename=f'uploads/{fname}')
                break
    return dict(profile_url=profile_url)


@app.route('/upload_profile_photo', methods=['POST'])
def upload_profile_photo():
    if 'username' not in session:
        flash('You must be logged in to upload a profile photo.')
        return redirect(url_for('login'))
    if 'profile_photo' not in request.files:
        flash('No file part in the request.')
        return redirect(request.referrer or url_for('dashboard'))
    file = request.files['profile_photo']
    if file.filename == '':
        flash('No selected file.')
        return redirect(request.referrer or url_for('dashboard'))
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    # Allow common web image formats; HEIC/HEIF will be converted when possible
    allowed = ('.png', '.jpg', '.jpeg', '.gif', '.heic', '.heif')
    if ext not in allowed:
        flash('Unsupported file type. Use png/jpg/gif/heic.')
        return redirect(request.referrer or url_for('dashboard'))

    # Handle HEIC/HEIF conversion if available (pyheif + pillow)
    if ext in ('.heic', '.heif'):
        try:
            # read file bytes
            data = file.read()
            try:
                import pyheif
                from PIL import Image
            except Exception:
                raise RuntimeError('HEIC conversion libraries not installed')

            heif_file = pyheif.read(data)
            # Create PIL image from HEIF data
            image = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                "raw",
                heif_file.mode,
                heif_file.stride,
            )
            # Save as PNG for browser compatibility
            save_name = f"{session['username']}_profile.png"
            save_path = os.path.join(UPLOAD_FOLDER, save_name)
            image.save(save_path, format='PNG')
            flash('Profile photo uploaded and converted to PNG.')
            return redirect(request.referrer or url_for('dashboard'))
        except Exception as e:
            # conversion failed; attempt to save original file so user has a backup
            try:
                file.stream.seek(0)
            except Exception:
                pass
            save_name = f"{session['username']}_profile{ext}"
            save_path = os.path.join(UPLOAD_FOLDER, save_name)
            file.save(save_path)
            flash('Uploaded HEIC but conversion not available; file saved. Your browser may not display HEIC images.')
            return redirect(request.referrer or url_for('dashboard'))

    # Normal image types: save directly
    save_name = f"{session['username']}_profile{ext}"
    save_path = os.path.join(UPLOAD_FOLDER, save_name)
    file.save(save_path)
    flash('Profile photo uploaded successfully.')
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        # If DB not available, fallback to a dev-mode signup (no persistence)
        if not MYSQL_AVAILABLE:
            flash("Signup simulated (dev mode). Please log in.")
            return redirect(url_for('login'))
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            execute_with_fallback(cursor, conn, "SELECT * FROM Account WHERE username=%s", (username,))
            if cursor.fetchone():
                flash("Username already exists!")
                conn.close()
                return render_template('signup.html')
            execute_with_fallback(cursor, conn, "INSERT INTO Account (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            conn.close()
            flash("Signup successful! Please log in.")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Signup failed (DB error): {e}")
            return render_template('signup.html')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # If DB is not available, allow a convenient dev-mode login
        if not MYSQL_AVAILABLE:
            session['username'] = username
            flash('Logged in (dev)')
            return redirect(url_for('dashboard'))
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            execute_with_fallback(cursor, conn, "SELECT password FROM Account WHERE username=%s", (username,))
            user = cursor.fetchone()
            conn.close()
            if user and check_password_hash(user[0], password):
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid credentials!")
        except Exception as e:
            # DB error: allow dev-mode login but inform (short message)
            session['username'] = username
            flash('Logged in (dev)')
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    # Fetch a few recent reservations to show on the dashboard
    recent_reservations = fetch_user_reservations(username, limit=3)
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
    return render_template('dashboard.html', username=username, search_results=search_results, recent_reservations=recent_reservations)

@app.route('/book/<int:flight_id>', methods=['GET'])
def book_preview(flight_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    # Get flight data from query parameter
    flight_data_json = request.args.get('flight_data')
    if not flight_data_json:
        flash("No flight data provided.")
        return redirect(url_for('dashboard'))
    try:
        flight_data = json.loads(flight_data_json)
    except Exception:
        # Sometimes the data may be url-encoded
        try:
            flight_data = json.loads(unquote(flight_data_json))
        except Exception:
            flash("Invalid flight data.")
            return redirect(url_for('dashboard'))
    return render_template('booking_confirmation.html', flight=flight_data, username=session['username'])

@app.route('/confirm_booking/<int:flight_id>', methods=['POST'])
def confirm_booking(flight_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    flight_data = json.loads(request.form['flight_data'])
    conn = get_db_connection()
    cursor, _dict_rows = make_cursor(conn)

    # Get user ID: try MySQL param style first, fall back to sqlite style
    try:
        execute_with_fallback(cursor, conn, "SELECT account_id FROM Account WHERE username=%s", (session['username'],))
        user = cursor.fetchone()
    except Exception:
        try:
            execute_with_fallback(cursor, conn, "SELECT account_id FROM Account WHERE username=?", (session['username'],))
            user = cursor.fetchone()
        except Exception:
            user = None

    if not user:
        # In dev-mode (sqlite fallback) create the user automatically so booking can proceed
        if not MYSQL_AVAILABLE:
            try:
                cursor.execute("INSERT INTO Account (username, password) VALUES (?, ?)", (session['username'], ''))
                conn.commit()
                user_id = cursor.lastrowid
            except Exception:
                # try MySQL param style as a last resort
                cursor.execute("INSERT INTO Account (username, password) VALUES (%s, %s)", (session['username'], ''))
                conn.commit()
                user_id = cursor.lastrowid
        else:
            conn.close()
            flash("User not found.")
            return redirect(url_for('login'))
    else:
        # fetch account id from row; handle sqlite Row or MySQL tuple/dict
        if isinstance(user, dict):
            user_id = user.get('account_id')
        else:
            # sqlite3.Row supports indexing by column name
            try:
                user_id = user['account_id']
            except Exception:
                # fallback for mysql tuple
                user_id = user[0]

    # Extract flight details from Amadeus data
    flight = flight_data['itineraries'][0]['segments'][0]
    airline = flight['carrierCode']
    origin = flight['departure']['iataCode']
    destination = flight['arrival']['iataCode']
    departure_time = flight['departure']['at']
    arrival_time = flight['arrival']['at']
    seats_available = flight_data.get('numberOfBookableSeats', 1)

    # Ensure airline exists in airline table
    execute_with_fallback(cursor, conn, "SELECT code FROM airline WHERE code=%s", (airline,))
    if not cursor.fetchone():
        airline_name = AIRLINE_NAMES.get(airline, airline)
        execute_with_fallback(cursor, conn, "INSERT INTO airline (code, name) VALUES (%s, %s)", (airline, airline_name))
        conn.commit()

    # Use correct column names: dep_port and arri_port
    execute_with_fallback(cursor, conn, """
        SELECT flight_no FROM Flight
        WHERE airline_code=%s AND dep_port=%s AND arri_port=%s AND dep_time=%s
    """, (airline, origin, destination, departure_time))
    flight_row = cursor.fetchone()

    db_flight_id = None
    if flight_row:
        # handle dict-like rows (MySQL) and tuple/sequence rows (sqlite)
        try:
            db_flight_id = flight_row.get('flight_no')
        except Exception:
            try:
                db_flight_id = flight_row[0]
            except Exception:
                db_flight_id = None
    if not db_flight_id:
        execute_with_fallback(cursor, conn, """
            INSERT INTO Flight (airline_code, dep_port, arri_port, dep_time, arri_time, booked_seats)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (airline, origin, destination, departure_time, arrival_time, seats_available))
        # For sqlite the lastrowid is available on cursor; for MySQL also available
        try:
            db_flight_id = cursor.lastrowid
        except Exception:
            # fallback: try to fetch the inserted row id by querying recently inserted matching row
            try:
                execute_with_fallback(cursor, conn, "SELECT flight_no FROM Flight WHERE airline_code=%s AND dep_port=%s AND arri_port=%s AND dep_time=%s", (airline, origin, destination, departure_time))
                fr = cursor.fetchone()
                try:
                    db_flight_id = fr.get('flight_no')
                except Exception:
                    db_flight_id = fr[0] if fr else None
            except Exception:
                db_flight_id = None

    # Insert reservation
    execute_with_fallback(cursor, conn, """
        INSERT INTO FlightReservation (user_id, flight_no)
        VALUES (%s, %s)
    """, (user_id, db_flight_id))
    conn.commit()
    conn.close()
    flash("Flight booked successfully!")
    return redirect(url_for('reservations'))


@app.route('/reservations')
def reservations():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor, _dict_rows = make_cursor(conn)
    try:
        execute_with_fallback(cursor, conn, "SELECT account_id FROM Account WHERE username=%s", (session['username'],))
        user = cursor.fetchone()
    except Exception:
        # sqlite param style
        execute_with_fallback(cursor, conn, "SELECT account_id FROM Account WHERE username=?", (session['username'],))
        user = cursor.fetchone()
    if not user:
        conn.close()
        flash("User not found.")
        return redirect(url_for('login'))
    user_id = user['account_id']
    # Fetch reservations and then resolve flight details per reservation.
    execute_with_fallback(cursor, conn, "SELECT * FROM FlightReservation WHERE user_id = %s ORDER BY creation_date DESC", (user_id,))
    raw_rows = cursor.fetchall()
    conn.close()

    def _parse_dt(v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            s = v.strip()
            if s.endswith('Z'):
                s = s[:-1]
            for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(s, fmt)
                except Exception:
                    continue
        return v

    reservations = []
    for row in raw_rows:
        try:
            res_id = row.get('id') or row.get('reservation_number')
        except Exception:
            try:
                res_id = row[0]
            except Exception:
                res_id = None
        try:
            flight_no = row.get('flight_no')
        except Exception:
            try:
                flight_no = row[2]
            except Exception:
                flight_no = None

        airline_code = dep_port = arri_port = dep_time = arri_time = None
        creation_date = None
        if flight_no:
            try:
                execute_with_fallback(cursor, conn, "SELECT airline_code, dep_port, arri_port, dep_time, arri_time FROM Flight WHERE flight_no = %s", (flight_no,))
                frow = cursor.fetchone()
                try:
                    airline_code = frow['airline_code']
                    dep_port = frow['dep_port']
                    arri_port = frow['arri_port']
                    dep_time = frow['dep_time']
                    arri_time = frow['arri_time']
                except Exception:
                    try:
                        airline_code, dep_port, arri_port, dep_time, arri_time = frow
                    except Exception:
                        pass
            except Exception:
                pass

        try:
            creation_date = row.get('creation_date')
        except Exception:
            try:
                creation_date = row[3]
            except Exception:
                creation_date = None

        reservations.append({
            'airline_code': airline_code,
            'dep_port': dep_port,
            'arri_port': arri_port,
            'dep_time': _parse_dt(dep_time),
            'arri_time': _parse_dt(arri_time),
            'creation_date': _parse_dt(creation_date),
        })

    return render_template('reservations.html', reservations=reservations)

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('login'))


@app.route('/cancel_reservation', methods=['POST'])
def cancel_reservation():
    if 'username' not in session:
        return redirect(url_for('login'))
    res_id = request.form.get('reservation_id')
    if not res_id:
        flash('No reservation specified.')
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    cursor, _ = make_cursor(conn)
    # Verify ownership: find user id and match reservation
    try:
        execute_with_fallback(cursor, conn, "SELECT account_id FROM Account WHERE username=%s", (session['username'],))
        user = cursor.fetchone()
    except Exception:
        execute_with_fallback(cursor, conn, "SELECT account_id FROM Account WHERE username=?", (session['username'],))
        user = cursor.fetchone()
    if not user:
        conn.close()
        flash('User not found.')
        return redirect(url_for('dashboard'))
    try:
        user_id = user['account_id']
    except Exception:
        user_id = user[0]

    # Check reservation owner
    execute_with_fallback(cursor, conn, "SELECT user_id FROM FlightReservation WHERE id=%s", (res_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        flash('Reservation not found.')
        return redirect(url_for('dashboard'))
    try:
        owner_id = row['user_id']
    except Exception:
        owner_id = row[0]
    if int(owner_id) != int(user_id):
        conn.close()
        flash('You are not authorized to cancel this reservation.')
        return redirect(url_for('dashboard'))

    # delete reservation
    execute_with_fallback(cursor, conn, "DELETE FROM FlightReservation WHERE id=%s", (res_id,))
    conn.commit()
    conn.close()
    flash('Reservation cancelled.')
    return redirect(url_for('dashboard'))

@app.route('/')
def home():
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)