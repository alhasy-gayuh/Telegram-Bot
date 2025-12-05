"""
OPTIONAL: OCR Callback Endpoint menggunakan FastAPI
Endpoint ini menerima hasil OCR dari n8n

CATATAN: File ini OPSIONAL dan untuk future implementation.
Bot utama (bot.py) sudah bisa jalan tanpa file ini.

Jika ingin mengaktifkan OCR callback:
1. Install FastAPI dan uvicorn (uncomment di requirements.txt)
2. Jalankan file ini terpisah: uvicorn ocr_endpoint:app --host 0.0.0.0 --port 8000
3. Set N8N_OCR_URL di .env mengarah ke endpoint ini
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Toko Bot OCR Callback")

# Load config
config = Config()


class OCRResult(BaseModel):
    """Model untuk hasil OCR dari n8n"""
    chat_id: int
    message_id: int
    is_tf_receipt: bool
    amount: Optional[int] = None
    raw_text: Optional[str] = None
    confidence: Optional[float] = None


@app.post("/ocr-transfer-result")
async def ocr_transfer_result(result: OCRResult):
    """
    Endpoint untuk menerima callback hasil OCR dari n8n

    Expected payload dari n8n:
    {
        "chat_id": 123456789,
        "message_id": 987654,
        "is_tf_receipt": true,
        "amount": 500000,
        "raw_text": "Transfer berhasil Rp500.000...",
        "confidence": 0.95
    }
    """
    try:
        logger.info(f"OCR result received: {result.dict()}")

        # Inisialisasi bot
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)

        if result.is_tf_receipt and result.amount:
            # Format pesan konfirmasi
            message = (
                f"🔍 *OCR Detected*\n\n"
                f"Terbaca: *Transfer Masuk*\n"
                f"Jumlah: *Rp{result.amount:,}*\n\n"
                f"Simpan sebagai transaksi hari ini?"
            )

            if result.confidence:
                message += f"\n_Confidence: {result.confidence*100:.1f}%_"

            # Buat inline keyboard untuk konfirmasi
            keyboard = [
                [
                    InlineKeyboardButton("✅ Simpan", callback_data=f"ocr_save_{result.amount}_{result.message_id}"),
                    InlineKeyboardButton("❌ Batal", callback_data=f"ocr_cancel_{result.message_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Kirim pesan ke Telegram
            await bot.send_message(
                chat_id=result.chat_id,
                text=message,
                reply_to_message_id=result.message_id,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

            logger.info(f"Confirmation message sent for amount {result.amount}")

        else:
            # Bukan bukti transfer atau gagal detect amount
            if result.raw_text:
                message = (
                    f"🔍 *OCR Processed*\n\n"
                    f"Gambar diproses tapi tidak terdeteksi sebagai bukti transfer yang valid.\n\n"
                    f"_Raw text: {result.raw_text[:100]}..._"
                )
            else:
                message = "🔍 Gambar diproses tapi tidak ada teks yang terdeteksi."

            await bot.send_message(
                chat_id=result.chat_id,
                text=message,
                reply_to_message_id=result.message_id,
                parse_mode='Markdown'
            )

        return {"status": "success", "message": "OCR result processed"}

    except Exception as e:
        logger.error(f"Error processing OCR result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "toko-bot-ocr-callback"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Toko Bot OCR Callback",
        "endpoints": {
            "ocr_callback": "/ocr-transfer-result",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = config.OCR_CALLBACK_PORT
    uvicorn.run(app, host="0.0.0.0", port=port)
