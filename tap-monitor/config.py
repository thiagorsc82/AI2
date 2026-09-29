import os
from dotenv import load_dotenv

load_dotenv()

# Cidades europeias com operação da TAP (catálogo; os ativos vêm de DESTINATIONS)
CATALOG = {
    "LIS": "Lisboa", "OPO": "Porto", "FAO": "Faro", "FNC": "Funchal",
    "MAD": "Madri", "BCN": "Barcelona", "CDG": "Paris", "LHR": "Londres",
    "FRA": "Frankfurt", "MUC": "Munique", "FCO": "Roma", "MXP": "Milão",
    "AMS": "Amsterdã", "BRU": "Bruxelas", "GVA": "Genebra", "ZRH": "Zurique",
    "CPH": "Copenhague", "DUB": "Dublin", "ATH": "Atenas", "VIE": "Viena",
}

PROVIDER = os.getenv("PROVIDER", "demo").lower()
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
ORIGIN = os.getenv("ORIGIN", "BEL")
CURRENCY = os.getenv("CURRENCY", "BRL")
DAYS_AHEAD = [int(x) for x in os.getenv("DAYS_AHEAD", "60").split(",") if x.strip()]
TRIP_LENGTH_DAYS = int(os.getenv("TRIP_LENGTH_DAYS", "0"))
DESTINATIONS = [d.strip().upper() for d in os.getenv("DESTINATIONS", "LIS,OPO,MAD,BCN,CDG,FCO").split(",") if d.strip()]
INTERVAL_MIN = int(os.getenv("CHECK_INTERVAL_MINUTES", "60"))
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "prices.db"))
