"""
database.py — SQLite persistence layer.

- Local dev and production: SQLite (CLASSIFIER_DB_PATH env var, default historial_clasificaciones.db)
"""

import csv
import logging
import os
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("CLASSIFIER_DB_PATH", "historial_clasificaciones.db")
CSV_PATH = "historial_clasificaciones.csv"

# ── Schema ───────────────────────────────────────────────────────────────────

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS registros (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           TEXT    NOT NULL,
    especie             TEXT,
    nombre_cientifico   TEXT,
    confianza           REAL,
    modo                TEXT,
    latitude            REAL,
    longitude           REAL,
    gps_source          TEXT,
    estado_conservacion TEXT,
    condicion_rastro    TEXT,
    tamanio_estimado    TEXT,
    hora_anidado        TEXT,
    accion_inmediata    TEXT
)
"""

_INSERT_SQL = """
    INSERT INTO registros
        (timestamp, especie, nombre_cientifico, confianza,
         modo, latitude, longitude, gps_source,
         estado_conservacion, condicion_rastro,
         tamanio_estimado, hora_anidado, accion_inmediata)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
"""

# ── Internal helpers ─────────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _float_or_none(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create the database/table if they don't exist, then migrate CSV."""
    try:
        conn = _conn()
        try:
            conn.execute(_CREATE_TABLE)
            conn.commit()
        finally:
            conn.close()
        logger.info("DB initialized (sqlite:%s)", DB_PATH)
        _migrate_csv_to_db()
    except Exception as exc:
        logger.error("Failed to initialize SQLite DB: %s", exc)


def _migrate_csv_to_db() -> None:
    """Import CSV records into the DB the first time (idempotent)."""
    if not os.path.exists(CSV_PATH):
        return

    try:
        conn = _conn()
        try:
            count = conn.execute("SELECT COUNT(*) FROM registros").fetchone()[0]
            if count > 0:
                return
            migrated = 0
            with open(CSV_PATH, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    conn.execute(_INSERT_SQL, _csv_row_to_params(row))
                    migrated += 1
            conn.commit()
        finally:
            conn.close()

        if migrated:
            logger.info("Migrated %d CSV records to DB", migrated)
    except Exception as exc:
        logger.error("CSV → DB migration failed: %s", exc)


def _csv_row_to_params(row: dict) -> tuple:
    return (
        row.get("timestamp", ""),
        row.get("especie", ""),
        row.get("nombre_cientifico", ""),
        _float_or_none(row.get("confianza")),
        row.get("modo", ""),
        _float_or_none(row.get("latitude")),
        _float_or_none(row.get("longitude")),
        row.get("gps_source") or None,
        row.get("estado_conservacion") or None,
        row.get("condicion_rastro") or None,
        row.get("tamanio_estimado") or None,
        row.get("hora_anidado") or None,
        row.get("accion_inmediata") or None,
    )


def guardar_registro(result: dict, mode: str, lat=None, lon=None) -> None:
    """Persist a classification result.

    Args:
        result:  Dict returned by clasificar(), may include gps_source.
        mode:    'turtle' or 'wildlife'.
        lat/lon: Resolved coordinates (EXIF or manual). May be None.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    params = (
        timestamp,
        result.get("species", ""),
        result.get("scientific_name", ""),
        _float_or_none(result.get("confidence")),
        mode,
        _float_or_none(lat),
        _float_or_none(lon),
        result.get("gps_source") or None,
        result.get("conservation_status") or None,
        result.get("track_condition") or None,
        result.get("animal_size_estimate") or None,
        result.get("estimated_nesting_time") or None,
        result.get("immediate_action") or None,
    )
    try:
        conn = _conn()
        try:
            conn.execute(_INSERT_SQL, params)
            conn.commit()
        finally:
            conn.close()
        logger.info("Record saved (mode=%s, species=%s)", mode, result.get("species"))
    except Exception as exc:
        logger.error("Failed to save record: %s", exc)
        # Do NOT re-raise — classification result is returned regardless.


def obtener_historial() -> list[dict]:
    """Return all records as list[dict], newest first."""
    try:
        conn = _conn()
        try:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM registros ORDER BY id DESC"
            ).fetchall()]
        finally:
            conn.close()
    except Exception as exc:
        logger.error("Failed to read history: %s", exc)
        return []


def obtener_historial_con_gps() -> list[dict]:
    """Return only records that have valid lat/lon coordinates."""
    sql = """
        SELECT * FROM registros
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY id DESC
    """
    try:
        conn = _conn()
        try:
            return [dict(r) for r in conn.execute(sql).fetchall()]
        finally:
            conn.close()
    except Exception as exc:
        logger.error("Failed to read GPS history: %s", exc)
        return []
