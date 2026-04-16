import base64
import json
import os
import tempfile

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from gps_extractor import extract_gps

load_dotenv()

app = Flask(__name__)
CORS(app)

MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


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
        return jsonify({"error": str(e)}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.route("/history")
def history():
    """Devuelve el historial de clasificaciones como JSON."""
    import pandas as pd

    csv_path = "historial_clasificaciones.csv"
    if not os.path.exists(csv_path):
        return jsonify([])

    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
        df = df.where(pd.notna(df), other=None)
        rows = df.to_dict(orient="records")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/map")
def map_view():
    """Renderiza un mapa Leaflet con marcadores de clasificaciones."""
    import pandas as pd

    csv_path = "historial_clasificaciones.csv"
    if not os.path.exists(csv_path):
        return render_template("map.html", markers=[])

    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
        df = df.dropna(subset=["latitude", "longitude"])

        markers = []
        for _, row in df.iterrows():
            markers.append({
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "species": row.get("especie", ""),
                "confidence": float(row["confianza"]) if pd.notna(row.get("confianza")) else 0,
                "timestamp": row.get("timestamp", ""),
                "mode": row.get("modo", ""),
                "scientific_name": row.get("nombre_cientifico", ""),
                "immediate_action": row.get("accion_inmediata", "") or "",
            })

        return render_template("map.html", markers=markers)
    except Exception as e:
        return render_template("map.html", markers=[], error=str(e))


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
