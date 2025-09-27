import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
VEO_API_KEY = os.getenv('VEO_API_KEY')

# Add other API keys as needed
# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Validate required keys
def validate_api_keys():
    required_keys = ['GEMINI_API_KEY', 'VEO_API_KEY']
    missing_keys = [key for key in required_keys if not globals()[key]]
    
    if missing_keys:
        raise ValueError(f"Missing required API keys: {', '.join(missing_keys)}")
    
    return True
