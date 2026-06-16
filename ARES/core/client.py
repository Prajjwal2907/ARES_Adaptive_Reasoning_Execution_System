from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key = GEMINI_API_KEY)