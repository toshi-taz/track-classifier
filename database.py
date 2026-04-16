"""
database.py — SQLite persistence layer for Wildlife Track Classifier.

Responsibilities:
- Initialize the DB and create the `registros` table if needed.
- Migrate existing CSV records on first run (one-time, idempotent).
- Provide guardar_registro() and obtener_historial() used by the rest of the app.
"""

import csv
import logging
import os
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("CLASSIFIER_DB_PATH", "historial_clasificaciones.db")
CSV_PATH = "historial_clasificaciones.csv"

# ------------------------------------------------------------------
# Schema
# ------------------------------------------------------------------

CREATE_TABLE_SQL = """
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

# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _float_or_none(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def init_db() -> None:
    """Create the database and table if they don't exist, then migrate CSV."""
    try:
        with _get_connection() as conn:
            conn.execute(CREATE_TABLE_SQL)
            conn.commit()
        logger.info("DB initialized: %s", DB_PATH)
        _migrate_csv_to_db()
    except Exception as exc:
        logger.error("Failed to initialize DB: %s", exc)


def _migrate_csv_to_db() -> None:
    """Import CSV records into SQLite the first time (idempotent)."""
    if not os.path.exists(CSV_PATH):
        return

    try:
        with _get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM registros").fetchone()[0]
            if count > 0:
                # DB already has data — skip migration to avoid duplicates.
                return

            migrated = 0
            with open(CSV_PATH, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    conn.execute(
                        """
                        INSERT INTO registros
                            (timestamp, especie, nombre_cientifico, confianza,
                             modo, latitude, longitude, gps_source,
                             estado_conservacion, condicion_rastro,
                             tamanio_estimado, hora_anidado, accion_inmediata)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
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
                        ),
                    )
                    migrated += 1
            conn.commit()
            if migrated:
                print(f"✅ Migrados {migrated} registros de CSV a SQLite")
    except Exception as exc:
        logger.error("CSV → DB migration failed: %s", exc)


def guardar_registro(result: dict, mode: str, lat=None, lon=None) -> None:
    """Persist a classification result to SQLite.

    Args:
        result:  Dict returned by clasificar(), may include gps_source.
        mode:    'turtle' or 'wildlife'.
        lat/lon: Resolved coordinates (EXIF or manual). May be None.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO registros
                    (timestamp, especie, nombre_cientifico, confianza,
                     modo, latitude, longitude, gps_source,
                     estado_conservacion, condicion_rastro,
                     tamanio_estimado, hora_anidado, accion_inmediata)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
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
                ),
            )
            conn.commit()
        logger.info("Record saved to DB (mode=%s, species=%s)", mode, result.get("species"))
    except Exception as exc:
        logger.error("Failed to save record to DB: %s", exc)
        # Do NOT re-raise — classification result is returned regardless.


def obtener_historial() -> list[dict]:
    """Return all records as a list of plain dicts, newest first."""
    try:
        with _get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM registros ORDER BY id DESC"
            ).fetchall()
            return [dict(row) for row in rows]
    except Exception as exc:
        logger.error("Failed to read history from DB: %s", exc)
        return []


def obtener_historial_con_gps() -> list[dict]:
    """Return only records that have valid lat/lon coordinates."""
    try:
        with _get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM registros
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                ORDER BY id DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]
    except Exception as exc:
        logger.error("Failed to read GPS history from DB: %s", exc)
        return []
