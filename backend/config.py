import os
from dotenv import load_dotenv

load_dotenv()

# Optional: kept for future cloud LLM use, but not required in offline mode.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
