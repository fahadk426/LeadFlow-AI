from dotenv import load_dotenv
import os

load_dotenv()

OCEAN_API_KEY = os.getenv("OCEAN_API_KEY")
PROSPEO_API_KEY = os.getenv("PROSPEO_API_KEY")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")