"""
Client untuk Google Gemini API
Menangani OCR dan ekstraksi data dari gambar bukti transfer
"""

import os
import json
import logging
import google.generativeai as genai
from typing import Dict, Optional, Any
from config import Config

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        api_key = Config.GEMINI_API_KEY
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            self.model = None
            return

        try:
            genai.configure(api_key=api_key)
            # Menggunakan Gemini 2.0 Flash karena tersedia di list user
            # Mode flash sangat cocok untuk tugas OCR simpel
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("GeminiClient initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GeminiClient: {e}")
            self.model = None

    def analyze_transfer_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Menganalisa gambar bukti transfer menggunakan Gemini

        Args:
            image_data: Bytes data dari gambar

        Returns:
            Dict dengan format:
            {
                "is_transfer": bool,
                "amount": int,
                "confidence": float,
                "reason": str,
                "raw_response": str (optional)
            }
        """
        if not self.model:
            return {
                "is_transfer": False,
                "amount": 0,
                "confidence": 0.0,
                "reason": "Gemini client not initialized (API Key missing?)"
            }

        try:
            prompt = """
            Kamu adalah asisten keuangan pintar. Tugasmu adalah mengekstrak data dari gambar struk transfer, bukti pembayaran QRIS, atau mutasi bank.

            Analisa gambar ini dan berikan output HANYA dalam format JSON valid (tanpa markdown ```json ... ```).

            Struktur JSON yang diminta:
            {
                "is_transfer": boolean, // true jika ini adalah bukti transfer/pembayaran uang yang valid. false jika bukan (misal foto kucing, selfie, atau screenshot chat biasa).
                "amount": integer, // Nilai nominal uang dalam Rupiah. HANYA ANGKA, tanpa titik/koma desimal. Contoh: 125000. Jika tidak ditemukan, isi 0.
                "confidence": float, // Tingkat keyakinan kamu (0.0 - 1.0).
                "date": string, // Tanggal transaksi jika terlihat (format YYYY-MM-DD), atau null jika tidak ada.
                "reason": string // Alasan singkat kenapa kamu menganggap ini transfer atau bukan, dan dari mana angka didapat.
            }

            Mata uang default adalah IDR (Rupiah). Abaikan desimal .00 di akhir jika ada.
            Jika gambar buram atau tidak terbaca, set is_transfer = false.
            """

            # Gemini menerima list parts, bisa text dan image bytes
            response = self.model.generate_content([
                {'mime_type': 'image/jpeg', 'data': image_data},
                prompt
            ])

            # Clean up response text to ensure it's valid JSON
            text_response = response.text.strip()

            # Kadang Gemini membungkus dengan markdown code block
            if text_response.startswith('```json'):
                text_response = text_response.replace('```json', '', 1)
            if text_response.startswith('```'):
                text_response = text_response.replace('```', '', 1)
            if text_response.endswith('```'):
                text_response = text_response.replace('```', '', 1)

            text_response = text_response.strip()

            logger.info(f"Gemini raw response: {text_response[:100]}...")

            try:
                data = json.loads(text_response)

                # Validasi field penting
                if 'amount' in data and isinstance(data['amount'], (int, float)):
                    data['amount'] = int(data['amount'])
                else:
                    data['amount'] = 0

                if 'is_transfer' not in data:
                    data['is_transfer'] = False

                return data

            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from Gemini: {text_response}")
                return {
                    "is_transfer": False,
                    "amount": 0,
                    "confidence": 0.0,
                    "reason": "Gagal parsing respon AI"
                }

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return {
                "is_transfer": False,
                "amount": 0,
                "confidence": 0.0,
                "reason": f"Error sistem: {str(e)}"
            }
