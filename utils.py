"""
Helper functions untuk parsing dan formatting
"""

import re
from typing import Union


def parse_amount(text: str) -> int:
    """
    Parse string angka menjadi integer rupiah

    Mendukung format:
    - 4000
    - 4k, 4K (ribuan)
    - 4rb, 4 ribu
    - 4.000, 4,000 (dengan separator)
    - 4jt, 4 juta, 4.000.000
    - 4m, 4M (juta - million)
    - Penjumlahan: 2000 + 7000 + 8rb
    - Dengan koma: 2000, 7000, 8rb

    Returns: integer (rupiah)
    Raises: ValueError jika format tidak valid
    """
    if not text:
        raise ValueError("Input kosong")

    # Clean whitespace
    text = text.strip().lower()

    # Hilangkan prefix "rp" atau "Rp" jika ada
    text = re.sub(r'^rp\.?\s*', '', text, flags=re.IGNORECASE)

    # Deteksi jika ada operator + atau koma (untuk penjumlahan)
    if '+' in text or ',' in text:
        return parse_amount_with_sum(text)

    # Parse single amount (existing logic)
    return parse_single_amount(text)


def parse_single_amount(text: str) -> int:
    """
    Parse single amount (tanpa penjumlahan)
    Helper function untuk parse_amount
    """
    # Deteksi suffix multiplier
    multiplier = 1

    # Juta (jt, juta, m, million)
    if re.search(r'(jt|juta|m|million)


def format_rupiah(amount: Union[int, float]) -> str:
    """
    Format angka menjadi format Rupiah dengan separator titik

    Examples:
    - 1000 -> "Rp1.000"
    - 1234567 -> "Rp1.234.567"
    - -5000 -> "-Rp5.000"

    Returns: string formatted rupiah
    """
    # Handle negative
    is_negative = amount < 0
    amount = abs(amount)

    # Convert to int (rupiah tidak ada desimal)
    amount = int(amount)

    # Format dengan separator titik
    formatted = f"{amount:,}".replace(',', '.')

    # Add prefix
    if is_negative:
        return f"-Rp{formatted}"
    return f"Rp{formatted}"


def parse_date(text: str) -> str:
    """
    STUB: Parse natural date string menjadi YYYY-MM-DD
    Untuk future enhancement (misal: "kemarin", "minggu lalu", dll)

    Untuk sekarang, return format YYYY-MM-DD atau raise error
    """
    # TODO: Implementasi natural date parsing
    # Contoh: "kemarin" -> "2025-12-04"
    #         "minggu lalu" -> range
    #         "1 des" -> "2025-12-01"

    # Sementara, hanya support format YYYY-MM-DD
    if re.match(r'\d{4}-\d{2}-\d{2}', text):
        return text

    raise ValueError("Format tanggal harus YYYY-MM-DD (misal: 2025-12-05)")


def validate_transaction_type(tipe: str) -> bool:
    """
    Validasi apakah tipe transaksi valid
    """
    valid_types = ['modal', 'cash', 'tf', 'keluar', 'pos']
    return tipe.lower() in valid_types


def sanitize_text(text: str, max_length: int = 200) -> str:
    """
    Sanitize text input untuk menghindari injection atau overflow
    """
    if not text:
        return ''

    # Trim whitespace
    text = text.strip()

    # Limit length
    if len(text) > max_length:
        text = text[:max_length]

    # Remove control characters (kecuali newline dan tab)
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

    return text
, text):
        multiplier = 1_000_000
        text = re.sub(r'(jt|juta|m|million)


def format_rupiah(amount: Union[int, float]) -> str:
    """
    Format angka menjadi format Rupiah dengan separator titik

    Examples:
    - 1000 -> "Rp1.000"
    - 1234567 -> "Rp1.234.567"
    - -5000 -> "-Rp5.000"

    Returns: string formatted rupiah
    """
    # Handle negative
    is_negative = amount < 0
    amount = abs(amount)

    # Convert to int (rupiah tidak ada desimal)
    amount = int(amount)

    # Format dengan separator titik
    formatted = f"{amount:,}".replace(',', '.')

    # Add prefix
    if is_negative:
        return f"-Rp{formatted}"
    return f"Rp{formatted}"


def parse_date(text: str) -> str:
    """
    STUB: Parse natural date string menjadi YYYY-MM-DD
    Untuk future enhancement (misal: "kemarin", "minggu lalu", dll)

    Untuk sekarang, return format YYYY-MM-DD atau raise error
    """
    # TODO: Implementasi natural date parsing
    # Contoh: "kemarin" -> "2025-12-04"
    #         "minggu lalu" -> range
    #         "1 des" -> "2025-12-01"

    # Sementara, hanya support format YYYY-MM-DD
    if re.match(r'\d{4}-\d{2}-\d{2}', text):
        return text

    raise ValueError("Format tanggal harus YYYY-MM-DD (misal: 2025-12-05)")


def validate_transaction_type(tipe: str) -> bool:
    """
    Validasi apakah tipe transaksi valid
    """
    valid_types = ['modal', 'cash', 'tf', 'keluar', 'pos']
    return tipe.lower() in valid_types


def sanitize_text(text: str, max_length: int = 200) -> str:
    """
    Sanitize text input untuk menghindari injection atau overflow
    """
    if not text:
        return ''

    # Trim whitespace
    text = text.strip()

    # Limit length
    if len(text) > max_length:
        text = text[:max_length]

    # Remove control characters (kecuali newline dan tab)
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

    return text
, '', text).strip()
    # Ribu (k, rb, ribu, thousand)
    elif re.search(r'(k|rb|ribu|thousand)


def format_rupiah(amount: Union[int, float]) -> str:
    """
    Format angka menjadi format Rupiah dengan separator titik

    Examples:
    - 1000 -> "Rp1.000"
    - 1234567 -> "Rp1.234.567"
    - -5000 -> "-Rp5.000"

    Returns: string formatted rupiah
    """
    # Handle negative
    is_negative = amount < 0
    amount = abs(amount)

    # Convert to int (rupiah tidak ada desimal)
    amount = int(amount)

    # Format dengan separator titik
    formatted = f"{amount:,}".replace(',', '.')

    # Add prefix
    if is_negative:
        return f"-Rp{formatted}"
    return f"Rp{formatted}"


def parse_date(text: str) -> str:
    """
    STUB: Parse natural date string menjadi YYYY-MM-DD
    Untuk future enhancement (misal: "kemarin", "minggu lalu", dll)

    Untuk sekarang, return format YYYY-MM-DD atau raise error
    """
    # TODO: Implementasi natural date parsing
    # Contoh: "kemarin" -> "2025-12-04"
    #         "minggu lalu" -> range
    #         "1 des" -> "2025-12-01"

    # Sementara, hanya support format YYYY-MM-DD
    if re.match(r'\d{4}-\d{2}-\d{2}', text):
        return text

    raise ValueError("Format tanggal harus YYYY-MM-DD (misal: 2025-12-05)")


def validate_transaction_type(tipe: str) -> bool:
    """
    Validasi apakah tipe transaksi valid
    """
    valid_types = ['modal', 'cash', 'tf', 'keluar', 'pos']
    return tipe.lower() in valid_types


def sanitize_text(text: str, max_length: int = 200) -> str:
    """
    Sanitize text input untuk menghindari injection atau overflow
    """
    if not text:
        return ''

    # Trim whitespace
    text = text.strip()

    # Limit length
    if len(text) > max_length:
        text = text[:max_length]

    # Remove control characters (kecuali newline dan tab)
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

    return text
, text):
        multiplier = 1_000
        text = re.sub(r'(k|rb|ribu|thousand)


def format_rupiah(amount: Union[int, float]) -> str:
    """
    Format angka menjadi format Rupiah dengan separator titik

    Examples:
    - 1000 -> "Rp1.000"
    - 1234567 -> "Rp1.234.567"
    - -5000 -> "-Rp5.000"

    Returns: string formatted rupiah
    """
    # Handle negative
    is_negative = amount < 0
    amount = abs(amount)

    # Convert to int (rupiah tidak ada desimal)
    amount = int(amount)

    # Format dengan separator titik
    formatted = f"{amount:,}".replace(',', '.')

    # Add prefix
    if is_negative:
        return f"-Rp{formatted}"
    return f"Rp{formatted}"


def parse_date(text: str) -> str:
    """
    STUB: Parse natural date string menjadi YYYY-MM-DD
    Untuk future enhancement (misal: "kemarin", "minggu lalu", dll)

    Untuk sekarang, return format YYYY-MM-DD atau raise error
    """
    # TODO: Implementasi natural date parsing
    # Contoh: "kemarin" -> "2025-12-04"
    #         "minggu lalu" -> range
    #         "1 des" -> "2025-12-01"

    # Sementara, hanya support format YYYY-MM-DD
    if re.match(r'\d{4}-\d{2}-\d{2}', text):
        return text

    raise ValueError("Format tanggal harus YYYY-MM-DD (misal: 2025-12-05)")


def validate_transaction_type(tipe: str) -> bool:
    """
    Validasi apakah tipe transaksi valid
    """
    valid_types = ['modal', 'cash', 'tf', 'keluar', 'pos']
    return tipe.lower() in valid_types


def sanitize_text(text: str, max_length: int = 200) -> str:
    """
    Sanitize text input untuk menghindari injection atau overflow
    """
    if not text:
        return ''

    # Trim whitespace
    text = text.strip()

    # Limit length
    if len(text) > max_length:
        text = text[:max_length]

    # Remove control characters (kecuali newline dan tab)
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

    return text
, '', text).strip()

    # Hilangkan separator (titik, koma, spasi)
    text = text.replace('.', '').replace(',', '').replace(' ', '')

    # Parse angka
    try:
        amount = float(text) * multiplier

        # Validasi
        if amount < 0:
            raise ValueError("Jumlah tidak boleh negatif")

        # Convert ke integer (rupiah tidak ada desimal)
        return int(amount)

    except ValueError as e:
        if "could not convert" in str(e):
            raise ValueError(f"Format angka tidak valid: '{text}'")
        raise


def parse_amount_with_sum(text: str) -> int:
    """
    Parse amount dengan penjumlahan
    Contoh: "2000 + 7000 + 8rb" atau "2000, 7000, 8rb"

    Returns: total jumlah (integer)
    """
    # Replace koma dengan + untuk uniform processing
    text = text.replace(',', '+')

    # Split by +
    parts = text.split('+')

    total = 0
    parsed_amounts = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        try:
            amount = parse_single_amount(part)
            total += amount
            parsed_amounts.append(amount)
        except ValueError as e:
            raise ValueError(f"Error parsing '{part}': {str(e)}")

    if total == 0:
        raise ValueError("Tidak ada angka valid yang ditemukan")

    return total


def format_rupiah(amount: Union[int, float]) -> str:
    """
    Format angka menjadi format Rupiah dengan separator titik

    Examples:
    - 1000 -> "Rp1.000"
    - 1234567 -> "Rp1.234.567"
    - -5000 -> "-Rp5.000"

    Returns: string formatted rupiah
    """
    # Handle negative
    is_negative = amount < 0
    amount = abs(amount)

    # Convert to int (rupiah tidak ada desimal)
    amount = int(amount)

    # Format dengan separator titik
    formatted = f"{amount:,}".replace(',', '.')

    # Add prefix
    if is_negative:
        return f"-Rp{formatted}"
    return f"Rp{formatted}"


def parse_date(text: str) -> str:
    """
    STUB: Parse natural date string menjadi YYYY-MM-DD
    Untuk future enhancement (misal: "kemarin", "minggu lalu", dll)

    Untuk sekarang, return format YYYY-MM-DD atau raise error
    """
    # TODO: Implementasi natural date parsing
    # Contoh: "kemarin" -> "2025-12-04"
    #         "minggu lalu" -> range
    #         "1 des" -> "2025-12-01"

    # Sementara, hanya support format YYYY-MM-DD
    if re.match(r'\d{4}-\d{2}-\d{2}', text):
        return text

    raise ValueError("Format tanggal harus YYYY-MM-DD (misal: 2025-12-05)")


def validate_transaction_type(tipe: str) -> bool:
    """
    Validasi apakah tipe transaksi valid
    """
    valid_types = ['modal', 'cash', 'tf', 'keluar', 'pos']
    return tipe.lower() in valid_types


def sanitize_text(text: str, max_length: int = 200) -> str:
    """
    Sanitize text input untuk menghindari injection atau overflow
    """
    if not text:
        return ''

    # Trim whitespace
    text = text.strip()

    # Limit length
    if len(text) > max_length:
        text = text[:max_length]

    # Remove control characters (kecuali newline dan tab)
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

    return text
