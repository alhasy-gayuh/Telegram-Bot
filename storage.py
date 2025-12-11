"""
Storage layer untuk database SQLite
Layer ini bisa diganti dengan Google Sheets atau database lain di masa depan
"""

import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class Storage:
    """Class untuk handle penyimpanan data ke SQLite"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Inisialisasi database dan tabel"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabel untuk transaksi
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tanggal TEXT NOT NULL,
                waktu TEXT NOT NULL,
                tipe TEXT NOT NULL,
                jumlah REAL NOT NULL,
                sumber TEXT NOT NULL,
                keterangan TEXT,
                chat_id INTEGER,
                user_id INTEGER,
                message_id INTEGER,
                file_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Index untuk performa query
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tanggal
            ON transactions(tanggal)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tanggal_tipe
            ON transactions(tanggal, tipe)
        ''')

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def add_transaction(
        self,
        tanggal: str,
        waktu: str,
        tipe: str,
        jumlah: float,
        sumber: str,
        keterangan: str = '',
        chat_id: int = 0,
        user_id: int = 0,
        message_id: int = 0,
        file_id: str = None
    ) -> int:
        """
        Menambahkan transaksi baru
        Returns: transaction ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO transactions
            (tanggal, waktu, tipe, jumlah, sumber, keterangan,
             chat_id, user_id, message_id, file_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (tanggal, waktu, tipe, jumlah, sumber, keterangan,
              chat_id, user_id, message_id, file_id))

        transaction_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Transaction added: ID={transaction_id}, tipe={tipe}, jumlah={jumlah}")
        return transaction_id

    def get_transactions_by_date(self, tanggal: str) -> List[Tuple]:
        """
        Mengambil semua transaksi untuk tanggal tertentu
        Returns: List of tuples (id, tanggal, waktu, tipe, jumlah, sumber, keterangan, ...)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, tanggal, waktu, tipe, jumlah, sumber, keterangan,
                   chat_id, user_id, message_id, file_id, created_at
            FROM transactions
            WHERE tanggal = ?
            ORDER BY waktu ASC, created_at ASC
        ''', (tanggal,))

        results = cursor.fetchall()
        conn.close()

        return results

    def get_latest_by_type(self, tanggal: str, tipe: str) -> Optional[float]:
        """
        Mengambil nilai transaksi TERAKHIR untuk tipe tertentu pada tanggal tertentu
        Digunakan untuk modal, cash, dan pos (yang cuma ambil input terakhir)

        Returns: jumlah (float) atau None jika tidak ada
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT jumlah
            FROM transactions
            WHERE tanggal = ? AND tipe = ?
            ORDER BY waktu DESC, created_at DESC
            LIMIT 1
        ''', (tanggal, tipe))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def get_sum_by_type(self, tanggal: str, tipe: str) -> float:
        """
        Mengambil SUM dari semua transaksi dengan tipe tertentu pada tanggal tertentu
        Digunakan untuk tf dan pengeluaran (yang dijumlahkan semua)

        Returns: total jumlah (float)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COALESCE(SUM(jumlah), 0)
            FROM transactions
            WHERE tanggal = ? AND tipe = ?
        ''', (tanggal, tipe))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else 0.0

    def get_transactions_range(
        self,
        start_date: str,
        end_date: str
    ) -> List[Tuple]:
        """
        Mengambil transaksi dalam range tanggal
        Berguna untuk rekap mingguan/bulanan (future implementation)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, tanggal, waktu, tipe, jumlah, sumber, keterangan,
                   chat_id, user_id, message_id, file_id, created_at
            FROM transactions
            WHERE tanggal BETWEEN ? AND ?
            ORDER BY tanggal ASC, waktu ASC
        ''', (start_date, end_date))

        results = cursor.fetchall()
        conn.close()

        return results

    def delete_transaction(self, transaction_id: int) -> bool:
        """
        Menghapus transaksi berdasarkan ID
        Returns: True jika berhasil, False jika tidak ditemukan
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
        affected = cursor.rowcount

        conn.commit()
        conn.close()

        if affected > 0:
            logger.info(f"Transaction deleted: ID={transaction_id}")
            return True
        return False

<<<<<<< HEAD
    def update_transaction(self, transaction_id: int, jumlah: float = None, keterangan: str = None) -> bool:
        """
        Update transaksi (jumlah atau keterangan)
        Returns: True jika berhasil
=======
    def get_recent_transactions(self, tanggal: str, limit: int = 10) -> List[Tuple]:
        """
        Mengambil transaksi terbaru untuk tanggal tertentu
        Returns: List of tuples dengan ID untuk keperluan edit
>>>>>>> 3507ac5a1d5d14260d74c8b52cddb5a329425722
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

<<<<<<< HEAD
        if jumlah is not None:
            cursor.execute('UPDATE transactions SET jumlah = ? WHERE id = ?', (jumlah, transaction_id))

        if keterangan is not None:
            cursor.execute('UPDATE transactions SET keterangan = ? WHERE id = ?', (keterangan, transaction_id))

=======
        cursor.execute('''
            SELECT id, tanggal, waktu, tipe, jumlah, sumber, keterangan,
                   chat_id, user_id, message_id, file_id, created_at
            FROM transactions
            WHERE tanggal = ?
            ORDER BY created_at DESC, waktu DESC
            LIMIT ?
        ''', (tanggal, limit))

        results = cursor.fetchall()
        conn.close()

        return results

    def get_transaction_by_id(self, transaction_id: int) -> Optional[Tuple]:
        """
        Mengambil detail transaksi berdasarkan ID
        Returns: tuple atau None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, tanggal, waktu, tipe, jumlah, sumber, keterangan,
                   chat_id, user_id, message_id, file_id, created_at
            FROM transactions
            WHERE id = ?
        ''', (transaction_id,))

        result = cursor.fetchone()
        conn.close()

        return result

    def get_transaction_count_by_type(self, tanggal: str, tipe: str) -> int:
        """
        Menghitung jumlah transaksi dengan tipe tertentu pada tanggal tertentu
        Berguna untuk menampilkan "(3x)" di status
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*)
            FROM transactions
            WHERE tanggal = ? AND tipe = ?
        ''', (tanggal, tipe))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else 0

    def delete_all_transactions_by_date(self, tanggal: str) -> int:
        """
        Menghapus SEMUA transaksi pada tanggal tertentu
        Digunakan untuk fitur /reset
        Returns: jumlah transaksi yang dihapus
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM transactions WHERE tanggal = ?', (tanggal,))
        affected = cursor.rowcount

>>>>>>> 3507ac5a1d5d14260d74c8b52cddb5a329425722
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        if affected > 0:
<<<<<<< HEAD
            logger.info(f"Transaction updated: ID={transaction_id}")
            return True
        return False

    def get_recent_transactions(self, tanggal: str, limit: int = 10) -> List[Tuple]:
        """
        Mengambil transaksi terbaru untuk tanggal tertentu
        Returns: List of tuples dengan ID untuk keperluan edit
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, tanggal, waktu, tipe, jumlah, sumber, keterangan,
                   chat_id, user_id, message_id, file_id, created_at
            FROM transactions
            WHERE tanggal = ?
            ORDER BY created_at DESC, waktu DESC
            LIMIT ?
        ''', (tanggal, limit))

        results = cursor.fetchall()
        conn.close()

        return results

    def get_transaction_by_id(self, transaction_id: int) -> Optional[Tuple]:
        """
        Mengambil detail transaksi berdasarkan ID
        Returns: tuple atau None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, tanggal, waktu, tipe, jumlah, sumber, keterangan,
                   chat_id, user_id, message_id, file_id, created_at
            FROM transactions
            WHERE id = ?
        ''', (transaction_id,))

        result = cursor.fetchone()
        conn.close()

        return result

    def get_transaction_count_by_type(self, tanggal: str, tipe: str) -> int:
        """
        Menghitung jumlah transaksi dengan tipe tertentu pada tanggal tertentu
        Berguna untuk menampilkan "(3x)" di status
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*)
            FROM transactions
            WHERE tanggal = ? AND tipe = ?
        ''', (tanggal, tipe))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else 0

    def delete_all_transactions_by_date(self, tanggal: str) -> int:
        """
        Menghapus SEMUA transaksi pada tanggal tertentu
        Digunakan untuk fitur /reset
        Returns: jumlah transaksi yang dihapus
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM transactions WHERE tanggal = ?', (tanggal,))
        affected = cursor.rowcount

        conn.commit()
        conn.close()

        if affected > 0:
=======
>>>>>>> 3507ac5a1d5d14260d74c8b52cddb5a329425722
            logger.info(f"All transactions deleted for date: {tanggal}, count: {affected}")

        return affected

    def check_modal_exists_today(self, tanggal: str) -> bool:
        """
        Cek apakah sudah ada modal untuk hari ini
        Digunakan untuk warning jika user input modal 2x dalam sehari
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*)
            FROM transactions
            WHERE tanggal = ? AND tipe = 'modal'
        ''', (tanggal,))

        result = cursor.fetchone()
        conn.close()

        return result[0] > 0 if result else False
