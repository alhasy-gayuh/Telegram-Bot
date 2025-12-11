"""
Konfigurasi untuk bot
Menggunakan environment variables untuk sensitive data
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Config:
    """Configuration class untuk bot"""

    # Telegram Bot Token (WAJIB)
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN tidak ditemukan! Silakan set di file .env")

    # Database path
    DB_PATH = os.getenv('DB_PATH', 'toko_keuangan.db')

    # N8N OCR Service URL (untuk integrasi OCR, boleh kosong dulu)
    N8N_OCR_URL = os.getenv('N8N_OCR_URL', 'http://localhost:5678/webhook/ocr-transfer')

    # Threshold untuk status selisih (dalam Rupiah)
    THRESHOLD_SELISIH_KECIL = int(os.getenv('THRESHOLD_SELISIH_KECIL', '1000'))
    THRESHOLD_SELISIH_BESAR = int(os.getenv('THRESHOLD_SELISIH_BESAR', '5000'))

    # OCR Callback endpoint (jika menggunakan FastAPI/Flask)
    OCR_CALLBACK_PORT = int(os.getenv('OCR_CALLBACK_PORT', '8000'))
    OCR_CALLBACK_PATH = os.getenv('OCR_CALLBACK_PATH', '/ocr-transfer-result')

    # Gemini API Key
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
