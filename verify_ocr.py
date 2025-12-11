"""
Script verification untuk Gemini OCR Integration
"""
import os
import sys
from dotenv import load_dotenv

# Load env variables
load_dotenv()

try:
    from ocr_gemini import GeminiClient
except ImportError as e:
    print(f"❌ Failed to import ocr_gemini: {e}")
    sys.exit(1)

def test_initialization():
    print("Testing GeminiClient initialization...")
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠️ GEMINI_API_KEY not found in .env")
        print("Please add GEMINI_API_KEY=your_key_here to .env file")
    else:
        print(f"✅ Found GEMINI_API_KEY: {api_key[:4]}...{api_key[-4:]}")

    client = GeminiClient()
    if client.model:
        print("✅ GeminiClient initialized successfully with model gemini-1.5-flash")
    else:
        print("❌ GeminiClient failed to initialize (check API key)")

if __name__ == "__main__":
    test_initialization()
