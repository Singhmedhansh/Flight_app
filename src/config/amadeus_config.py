import os

from amadeus import Client
from dotenv import load_dotenv

load_dotenv()

amadeus_client_id = os.getenv("AMADEUS_CLIENT_ID")
amadeus_client_secret = os.getenv("AMADEUS_CLIENT_SECRET")

if not amadeus_client_id or not amadeus_client_secret:
    raise RuntimeError(
        "Missing Amadeus credentials. Set AMADEUS_CLIENT_ID and "
        "AMADEUS_CLIENT_SECRET in environment variables or a local .env file."
    )

amadeus = Client(
    client_id=amadeus_client_id,
    client_secret=amadeus_client_secret,
)