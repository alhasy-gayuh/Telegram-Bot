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

        # Tabel untuk rekap harian (v2)
        # Menyimpan snapshot rekap dengan versioning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                state TEXT NOT NULL CHECK(state IN ('DRAFT', 'FINAL', 'REVISED')),

                modal REAL NOT NULL DEFAULT 0,
                cash_akhir REAL NOT NULL DEFAULT 0,
                total_tf REAL NOT NULL DEFAULT 0,
                count_tf INTEGER NOT NULL DEFAULT 0,
                total_pengeluaran REAL NOT NULL DEFAULT 0,
                count_pengeluaran INTEGER NOT NULL DEFAULT 0,
                pos_total REAL NOT NULL DEFAULT 0,
                count_pos INTEGER NOT NULL DEFAULT 0,
                penjualan_cash REAL NOT NULL DEFAULT 0,
                omzet_manual REAL NOT NULL DEFAULT 0,
                selisih REAL NOT NULL DEFAULT 0,
                selisih_abs REAL NOT NULL DEFAULT 0,
                selisih_persen REAL NOT NULL DEFAULT 0,
                status_text TEXT NOT NULL DEFAULT '',
                status_icon TEXT NOT NULL DEFAULT '',

                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(date, version)
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_daily_summaries_date
            ON daily_summaries(date)
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

    def update_transaction(self, transaction_id: int, jumlah: float = None, keterangan: str = None) -> bool:
        """
        Update transaksi (jumlah atau keterangan)
        Returns: True jika berhasil
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if jumlah is not None:
            cursor.execute('UPDATE transactions SET jumlah = ? WHERE id = ?', (jumlah, transaction_id))

        if keterangan is not None:
            cursor.execute('UPDATE transactions SET keterangan = ? WHERE id = ?', (keterangan, transaction_id))

        conn.commit()
        affected = cursor.rowcount
        conn.close()

        if affected > 0:
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

    # ===== DAILY SUMMARIES METHODS (v2) =====

    def save_daily_summary(self, date: str, state: str, summary_data: dict, notes: str = None) -> int:
        """
        Simpan rekap harian dengan versioning otomatis.
        Jika sudah ada versi untuk tanggal tersebut, buat versi baru (version + 1).

        Args:
            date: Tanggal rekap (YYYY-MM-DD)
            state: 'DRAFT', 'FINAL', atau 'REVISED'
            summary_data: Dict hasil dari logic.calculate_daily_summary()
            notes: Catatan opsional

        Returns: summary ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Ambil versi terbaru untuk tanggal ini
        cursor.execute('''
            SELECT COALESCE(MAX(version), 0) FROM daily_summaries WHERE date = ?
        ''', (date,))
        latest_version = cursor.fetchone()[0]
        new_version = latest_version + 1

        cursor.execute('''
            INSERT INTO daily_summaries
            (date, version, state, modal, cash_akhir, total_tf, count_tf,
             total_pengeluaran, count_pengeluaran, pos_total, count_pos,
             penjualan_cash, omzet_manual, selisih, selisih_abs, selisih_persen,
             status_text, status_icon, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            date, new_version, state,
            summary_data.get('modal', 0),
            summary_data.get('cash_akhir', 0),
            summary_data.get('total_tf', 0),
            summary_data.get('count_tf', 0),
            summary_data.get('total_pengeluaran', 0),
            summary_data.get('count_pengeluaran', 0),
            summary_data.get('pos_total', 0),
            summary_data.get('count_pos', 0),
            summary_data.get('penjualan_cash', 0),
            summary_data.get('omzet_manual', 0),
            summary_data.get('selisih', 0),
            summary_data.get('selisih_abs', 0),
            summary_data.get('selisih_persen', 0),
            summary_data.get('status_text', ''),
            summary_data.get('status_icon', ''),
            notes
        ))

        summary_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Daily summary saved: date={date}, version={new_version}, state={state}")
        return summary_id

    def get_daily_summaries_by_date(self, date: str) -> List[Tuple]:
        """
        Ambil SEMUA versi rekap untuk tanggal tertentu.
        Berguna untuk melihat history revisi.

        Returns: List of tuples, sorted by version DESC (terbaru dulu)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, date, version, state, modal, cash_akhir, total_tf, count_tf,
                   total_pengeluaran, count_pengeluaran, pos_total, count_pos,
                   penjualan_cash, omzet_manual, selisih, selisih_abs, selisih_persen,
                   status_text, status_icon, notes, created_at
            FROM daily_summaries
            WHERE date = ?
            ORDER BY version DESC
        ''', (date,))

        results = cursor.fetchall()
        conn.close()

        return results

    def get_latest_summary_by_date(self, date: str) -> Optional[Tuple]:
        """
        Ambil rekap VERSI TERBARU untuk tanggal tertentu.
        Menggunakan MAX(version), bukan created_at, untuk konsistensi.

        Returns: Tuple atau None jika tidak ada
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, date, version, state, modal, cash_akhir, total_tf, count_tf,
                   total_pengeluaran, count_pengeluaran, pos_total, count_pos,
                   penjualan_cash, omzet_manual, selisih, selisih_abs, selisih_persen,
                   status_text, status_icon, notes, created_at
            FROM daily_summaries
            WHERE date = ? AND version = (
                SELECT MAX(version) FROM daily_summaries WHERE date = ?
            )
        ''', (date, date))

        result = cursor.fetchone()
        conn.close()

        return result

    def get_summaries_range(self, start_date: str, end_date: str) -> List[Tuple]:
        """
        Ambil rekap TERBARU per tanggal dalam range.
        Untuk rekap mingguan/bulanan, selalu pakai versi terbaru per tanggal.

        Returns: List of latest summaries, satu per tanggal, sorted by date ASC
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Subquery untuk ambil MAX(version) per date, lalu join
        cursor.execute('''
            SELECT ds.id, ds.date, ds.version, ds.state, ds.modal, ds.cash_akhir,
                   ds.total_tf, ds.count_tf, ds.total_pengeluaran, ds.count_pengeluaran,
                   ds.pos_total, ds.count_pos, ds.penjualan_cash, ds.omzet_manual,
                   ds.selisih, ds.selisih_abs, ds.selisih_persen, ds.status_text,
                   ds.status_icon, ds.notes, ds.created_at
            FROM daily_summaries ds
            INNER JOIN (
                SELECT date, MAX(version) as max_version
                FROM daily_summaries
                WHERE date BETWEEN ? AND ?
                GROUP BY date
            ) latest ON ds.date = latest.date AND ds.version = latest.max_version
            ORDER BY ds.date ASC
        ''', (start_date, end_date))

        results = cursor.fetchall()
        conn.close()

        return results

    def get_dates_with_summaries(self, start_date: str, end_date: str) -> List[str]:
        """
        Ambil daftar tanggal yang sudah punya rekap dalam range.
        Berguna untuk cek tanggal mana yang belum ada rekapnya.

        Returns: List of date strings
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT date FROM daily_summaries
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC
        ''', (start_date, end_date))

        results = [row[0] for row in cursor.fetchall()]
        conn.close()

        return results
