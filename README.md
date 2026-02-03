# Flight Booker

A Flask-based flight booking application with seat selection, confirmation, and digital ticketing.

## Features
- Flight search and filtering
- Seat selection flow
- Confirmation step before booking
- Digital ticket with QR code
- Reservations history

## Tech Stack
- Flask (Python)
- MySQL (via mysql-connector)
- Amadeus API (flight data)
- Tailwind CSS (CDN)

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure database credentials in `src/config/database_config.py`.
4. Run the app:
   ```bash
   python src/app.py
   ```

## Notes
- The app uses session-based storage for bookings in the UI flow.
- Ensure the MySQL database is reachable for auth and other DB-backed features.

## Project Structure
- `src/app.py`: Flask app and routes
- `src/templates/`: Jinja2 templates
- `src/static/`: CSS and assets
- `src/config/`: DB and API configuration
