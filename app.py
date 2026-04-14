import os
import json
import tempfile
from datetime import datetime

from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

SPECIES_IMAGES = {
    "Chelonia mydas": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Chelonia_mydas_is_going_to_the_sea.jpg/640px-Chelonia_mydas_is_going_to_the_sea.jpg",
    "Green sea turtle": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Chelonia_mydas_is_going_to_the_sea.jpg/640px-Chelonia_mydas_is_going_to_the_sea.jpg",
    "Caretta caretta": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Loggerhead_sea_turtle.jpg/640px-Loggerhead_sea_turtle.jpg",
    "Loggerhead sea turtle": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Loggerhead_sea_turtle.jpg/640px-Loggerhead_sea_turtle.jpg",
    "Eretmochelys imbricata": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Hawksbill_sea_turtle_wikipedia.jpg/640px-Hawksbill_sea_turtle_wikipedia.jpg",
    "Hawksbill sea turtle": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Hawksbill_sea_turtle_wikipedia.jpg/640px-Hawksbill_sea_turtle_wikipedia.jpg",
    "Dermochelys coriacea": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Leatherback_sea_turtle_Tinglar_USVI_%285765107100%29.jpg/640px-Leatherback_sea_turtle_Tinglar_USVI_%285765107100%29.jpg",
    "Leatherback sea turtle": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Leatherback_sea_turtle_Tinglar_USVI_%285765107100%29.jpg/640px-Leatherback_sea_turtle_Tinglar_USVI_%285765107100%29.jpg",
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/classify", methods=["POST"])
def classify():
    if "image" not in request.files:
        return jsonify({"error": "No se recibió ninguna imagen"}), 400

    file = request.files["image"]
    mode = request.form.get("mode", "turtle")

    if file.filename == "":
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Formato no válido. Usa JPG, PNG o WEBP"}), 400

    if mode not in ("turtle", "wildlife"):
        return jsonify({"error": "Modo inválido. Usa 'turtle' o 'wildlife'"}), 400

    suffix = "." + secure_filename(file.filename).rsplit(".", 1)[-1].lower()
    tmp_path = None
    result = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            file.save(tmp_path)

        from classifier import clasificar, guardar_historial

        result = clasificar(tmp_path, mode)
        result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result["mode"] = mode
        result["reference_image"] = SPECIES_IMAGES.get(
            result.get("species", ""),
            SPECIES_IMAGES.get(result.get("scientific_name", ""), ""),
        )

        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({"error": "Gemini devolvió una respuesta no válida. Intenta de nuevo."}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # guardar_historial must run while tmp_path still exists on disk
        if result is not None and tmp_path:
            try:
                from classifier import guardar_historial
                guardar_historial(tmp_path, result, mode)
            except Exception:
                pass
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.route("/history")
def history():
    import pandas as pd

    csv_path = "historial_clasificaciones.csv"
    if not os.path.exists(csv_path):
        return jsonify([])

    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
        df = df.sort_values("timestamp", ascending=False)
        # Replace NaN with None so JSON serialisation gives null
        df = df.where(pd.notnull(df), None)
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
