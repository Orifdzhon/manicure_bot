# =============================================================
#  database/db.py — инициализация и запросы SQLite
# =============================================================
import sqlite3
import os
from config import config


def get_connection() -> sqlite3.Connection:
    """Возвращает соединение с базой данных."""
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row  # доступ по имени столбца
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Создаёт таблицы, если они ещё не существуют."""
    with get_connection() as conn:
        conn.executescript("""
        -- Рабочие дни
        CREATE TABLE IF NOT EXISTS working_days (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            date      TEXT UNIQUE NOT NULL,   -- YYYY-MM-DD
            is_closed INTEGER NOT NULL DEFAULT 0  -- 1 = день закрыт
        );

        -- Временны́е слоты
        CREATE TABLE IF NOT EXISTS time_slots (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            day_id     INTEGER NOT NULL REFERENCES working_days(id) ON DELETE CASCADE,
            time       TEXT NOT NULL,          -- HH:MM
            is_booked  INTEGER NOT NULL DEFAULT 0
        );

        -- Записи клиентов
        CREATE TABLE IF NOT EXISTS bookings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            slot_id     INTEGER NOT NULL UNIQUE REFERENCES time_slots(id),
            name        TEXT NOT NULL,
            phone       TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)


# ─── рабочие дни ──────────────────────────────────────────────────────────────

def add_working_day(date: str) -> bool:
    """Добавляет рабочий день. Возвращает True при успехе."""
    with get_connection() as conn:
        try:
            conn.execute("INSERT OR IGNORE INTO working_days (date) VALUES (?)", (date,))
            return True
        except Exception:
            return False


def get_working_days() -> list[sqlite3.Row]:
    """Список всех рабочих дней (не закрытых)."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM working_days WHERE is_closed = 0 ORDER BY date"
        ).fetchall()


def close_day(date: str):
    """Помечает день как закрытый."""
    with get_connection() as conn:
        conn.execute("UPDATE working_days SET is_closed = 1 WHERE date = ?", (date,))


def open_day(date: str):
    """Снимает отметку закрытия."""
    with get_connection() as conn:
        conn.execute("UPDATE working_days SET is_closed = 0 WHERE date = ?", (date,))


def get_day(date: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM working_days WHERE date = ?", (date,)
        ).fetchone()


# ─── временны́е слоты ──────────────────────────────────────────────────────────

def add_time_slot(date: str, time: str) -> bool:
    """Добавляет слот на дату. Возвращает True при успехе."""
    with get_connection() as conn:
        day = conn.execute(
            "SELECT id FROM working_days WHERE date = ?", (date,)
        ).fetchone()
        if not day:
            return False
        try:
            conn.execute(
                "INSERT INTO time_slots (day_id, time) VALUES (?, ?)",
                (day["id"], time),
            )
            return True
        except Exception:
            return False


def delete_time_slot(slot_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM time_slots WHERE id = ?", (slot_id,))


def get_slots_for_date(date: str) -> list[sqlite3.Row]:
    """Все слоты для даты."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT ts.*, wd.date FROM time_slots ts
            JOIN working_days wd ON ts.day_id = wd.id
            WHERE wd.date = ?
            ORDER BY ts.time
            """,
            (date,),
        ).fetchall()


def get_free_slots_for_date(date: str) -> list[sqlite3.Row]:
    """Только свободные слоты для даты."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT ts.* FROM time_slots ts
            JOIN working_days wd ON ts.day_id = wd.id
            WHERE wd.date = ? AND ts.is_booked = 0 AND wd.is_closed = 0
            ORDER BY ts.time
            """,
            (date,),
        ).fetchall()


def get_slot(slot_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT ts.*, wd.date FROM time_slots ts
            JOIN working_days wd ON ts.day_id = wd.id
            WHERE ts.id = ?
            """,
            (slot_id,),
        ).fetchone()


# ─── записи ───────────────────────────────────────────────────────────────────

def get_user_booking(user_id: int) -> sqlite3.Row | None:
    """Возвращает активную запись пользователя (если есть)."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT b.*, ts.time, wd.date FROM bookings b
            JOIN time_slots ts ON b.slot_id = ts.id
            JOIN working_days wd ON ts.day_id = wd.id
            WHERE b.user_id = ?
            """,
            (user_id,),
        ).fetchone()


def create_booking(user_id: int, slot_id: int, name: str, phone: str) -> bool:
    """Создаёт запись и помечает слот занятым. Возвращает True при успехе."""
    with get_connection() as conn:
        try:
            conn.execute(
                "INSERT INTO bookings (user_id, slot_id, name, phone) VALUES (?, ?, ?, ?)",
                (user_id, slot_id, name, phone),
            )
            conn.execute("UPDATE time_slots SET is_booked = 1 WHERE id = ?", (slot_id,))
            return True
        except Exception:
            return False


def cancel_booking_by_user(user_id: int) -> sqlite3.Row | None:
    """Отменяет запись пользователя. Возвращает строку отменённой записи."""
    with get_connection() as conn:
        booking = conn.execute(
            "SELECT * FROM bookings WHERE user_id = ?", (user_id,)
        ).fetchone()
        if booking:
            conn.execute(
                "UPDATE time_slots SET is_booked = 0 WHERE id = ?",
                (booking["slot_id"],),
            )
            conn.execute("DELETE FROM bookings WHERE id = ?", (booking["id"],))
        return booking


def cancel_booking_by_slot(slot_id: int) -> sqlite3.Row | None:
    """Отменяет запись по ID слота (для администратора)."""
    with get_connection() as conn:
        booking = conn.execute(
            "SELECT * FROM bookings WHERE slot_id = ?", (slot_id,)
        ).fetchone()
        if booking:
            conn.execute("UPDATE time_slots SET is_booked = 0 WHERE id = ?", (slot_id,))
            conn.execute("DELETE FROM bookings WHERE id = ?", (booking["id"],))
        return booking


def get_booking_for_slot(slot_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM bookings WHERE slot_id = ?", (slot_id,)
        ).fetchone()


def get_all_bookings_for_date(date: str) -> list[sqlite3.Row]:
    """Все записи на дату (для администратора)."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT b.*, ts.time, wd.date FROM bookings b
            JOIN time_slots ts ON b.slot_id = ts.id
            JOIN working_days wd ON ts.day_id = wd.id
            WHERE wd.date = ?
            ORDER BY ts.time
            """,
            (date,),
        ).fetchall()


def get_all_future_bookings() -> list[sqlite3.Row]:
    """Все будущие записи (для восстановления задач планировщика)."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT b.*, ts.time, wd.date FROM bookings b
            JOIN time_slots ts ON b.slot_id = ts.id
            JOIN working_days wd ON ts.day_id = wd.id
            WHERE wd.date >= date('now')
            ORDER BY wd.date, ts.time
            """,
        ).fetchall()
