import base64
import json
import logging
import os
import secrets
import tempfile
from functools import wraps

from flask import Flask, request, jsonify, render_template, send_from_directory, Response
from flask_cors import CORS
from dotenv import load_dotenv
from gps_extractor import extract_gps
from database import init_db, obtener_historial, obtener_historial_con_gps

load_dotenv()

logger = logging.getLogger(__name__)

app = Flask(__name__)

# ── CORS: restrict to configured origins (default: localhost only) ──────────
_raw_origins = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:5000,http://127.0.0.1:5000"
)
CORS(app, origins=[o.strip() for o in _raw_origins.split(",")])

# Initialize SQLite DB (and migrate CSV) at startup.
init_db()

# ── Upload limits ────────────────────────────────────────────────────────────
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB decoded

MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


# ── Security headers ─────────────────────────────────────────────────────────
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com; "
        "font-src https://fonts.gstatic.com; "
        "img-src 'self' data: blob: https://unpkg.com "
        "https://*.basemaps.cartocdn.com https://*.tile.openstreetmap.org; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )
    return response


# ── Optional Basic Auth for sensitive endpoints ──────────────────────────────
def _check_password(password: str) -> bool:
    app_password = os.environ.get("APP_PASSWORD", "")
    if not app_password:
        return True  # no password configured — open access (dev mode)
    return secrets.compare_digest(password.encode(), app_password.encode())


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not os.environ.get("APP_PASSWORD", ""):
            return f(*args, **kwargs)
        auth = request.authorization
        if not auth or not _check_password(auth.password):
            return Response(
                "Authentication required.",
                401,
                {"WWW-Authenticate": 'Basic realm="Track Classifier"'},
            )
        return f(*args, **kwargs)
    return decorated


def _decode_image(b64_data: str) -> tuple[bytes, str]:
    """Return (raw bytes, file extension) from a base64 string.

    Accepts both plain base64 and data-URI format:
        data:image/jpeg;base64,<data>
    """
    if b64_data.startswith("data:"):
        header, b64_data = b64_data.split(",", 1)
        mime = header.split(":")[1].split(";")[0]
    else:
        mime = "image/jpeg"

    suffix = MIME_TO_EXT.get(mime, ".jpg")
    return base64.b64decode(b64_data), suffix


@app.route("/sw.js")
def service_worker():
    """Serve SW from root so its scope covers the entire origin."""
    response = send_from_directory("static", "sw.js")
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/classify", methods=["POST"])
def classify():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON"}), 400

    b64_image = body.get("image")
    mode = body.get("mode", "turtle")
    manual_lat = body.get("latitude")
    manual_lon = body.get("longitude")

    if not b64_image:
        return jsonify({"error": "Missing 'image' field (base64)"}), 400

    if mode not in ("turtle", "wildlife"):
        return jsonify({"error": "Invalid mode. Use 'turtle' or 'wildlife'"}), 400

    try:
        image_bytes, suffix = _decode_image(b64_image)
    except Exception:
        return jsonify({"error": "Invalid base64 image data"}), 400

    if len(image_bytes) > MAX_IMAGE_BYTES:
        return jsonify({"error": "Image exceeds the maximum allowed size of 10 MB"}), 413

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        from classifier import clasificar, guardar_historial

        result = clasificar(tmp_path, mode)
        result["mode"] = mode

        # GPS resolution: EXIF first, then manual input
        gps = extract_gps(tmp_path)
        if gps:
            lat = gps["latitude"]
            lon = gps["longitude"]
            result["gps_source"] = "exif"
        elif manual_lat is not None and manual_lon is not None:
            try:
                lat = float(manual_lat)
                lon = float(manual_lon)
                result["gps_source"] = "manual"
            except (ValueError, TypeError):
                lat = lon = None
                result["gps_source"] = None
        else:
            lat = lon = None
            result["gps_source"] = None

        result["latitude"] = lat
        result["longitude"] = lon

        guardar_historial(tmp_path, result, mode, lat=lat, lon=lon)

        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({"error": "Gemini returned an invalid response. Please try again."}), 502
    except Exception as e:
        logger.error("classify error: %s", e)
        return jsonify({"error": "An internal error occurred. Please try again."}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.route("/history")
@require_auth
def history():
    """Devuelve el historial de clasificaciones como JSON (lee de SQLite)."""
    try:
        rows = obtener_historial()
        return jsonify(rows)
    except Exception as e:
        logger.error("history error: %s", e)
        return jsonify({"error": "Could not retrieve history."}), 500


@app.route("/map")
@require_auth
def map_view():
    """Renderiza un mapa Leaflet con marcadores de clasificaciones (lee de SQLite)."""
    try:
        rows = obtener_historial_con_gps()
        markers = [
            {
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "species": row.get("especie", ""),
                "confidence": row["confianza"] or 0,
                "timestamp": row.get("timestamp", ""),
                "mode": row.get("modo", ""),
                "scientific_name": row.get("nombre_cientifico", ""),
                "immediate_action": row.get("accion_inmediata") or "",
            }
            for row in rows
        ]
        return render_template("map.html", markers=markers)
    except Exception as e:
        logger.error("map error: %s", e)
        return render_template("map.html", markers=[])


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
