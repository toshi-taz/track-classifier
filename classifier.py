from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json
import argparse
import sys
import csv
from PIL import Image
import pathlib
from datetime import datetime
from gps_extractor import extract_gps

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

from prompts.species import TURTLE_PROMPT, GENERAL_WILDLIFE_PROMPT

HISTORIAL_FILE = "historial_clasificaciones.csv"

FIELDNAMES = [
    "timestamp", "especie", "nombre_cientifico", "confianza",
    "modo", "latitude", "longitude", "estado_conservacion", "accion_inmediata"
]


def _migrate_historial():
    """Ensure the CSV has the expected columns, migrating old-format files."""
    if not os.path.exists(HISTORIAL_FILE):
        return
    try:
        import pandas as pd
        df = pd.read_csv(HISTORIAL_FILE, encoding="utf-8")
        needs_migration = any(col not in df.columns for col in FIELDNAMES)
        if not needs_migration:
            return
        # Map old column names
        if "modo" not in df.columns and "mode" in df.columns:
            df.rename(columns={"mode": "modo"}, inplace=True)
        # Add missing columns as empty strings
        for col in FIELDNAMES:
            if col not in df.columns:
                df[col] = ""
        df = df[FIELDNAMES]
        df.to_csv(HISTORIAL_FILE, index=False, encoding="utf-8")
        print(f"✅ Historial migrado al nuevo esquema ({HISTORIAL_FILE})")
    except Exception as e:
        print(f"⚠️ No se pudo migrar el historial: {e}", file=sys.stderr)

def cargar_imagen(path):
    if not os.path.exists(path):
        print(f"❌ Error: imagen no encontrada en {path}")
        sys.exit(1)
    try:
        img = Image.open(path)
        print(f"✅ Imagen cargada: {path} ({img.size[0]}x{img.size[1]} px)")
        return path
    except Exception as e:
        print(f"❌ Error al cargar imagen: {e}")
        sys.exit(1)

def clasificar(image_path, mode="turtle"):
    cargar_imagen(image_path)
    prompt = TURTLE_PROMPT if mode == "turtle" else GENERAL_WILDLIFE_PROMPT

    print(f"\n🔍 Analizando imagen con Gemini Vision...")
    print(f"   Modo: {'Tortugas marinas' if mode == 'turtle' else 'Fauna general'}\n")

    image_bytes = pathlib.Path(image_path).read_bytes()
    ext = pathlib.Path(image_path).suffix.lower()
    mime = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime),
            prompt
        ]
    )

    text = response.text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    return json.loads(text)

def guardar_historial(image_path, result, mode, lat=None, lon=None):
    """Save classification to CSV history.

    lat/lon: resolved coordinates (EXIF or manual). If both are None and the
    caller is the CLI, we attempt EXIF extraction from image_path.
    """
    _migrate_historial()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # CLI path: caller didn't resolve GPS yet
    if lat is None and lon is None:
        try:
            gps = extract_gps(image_path)
            lat = gps.get("latitude") if gps else None
            lon = gps.get("longitude") if gps else None
        except Exception:
            pass

    file_exists = os.path.exists(HISTORIAL_FILE)
    with open(HISTORIAL_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "timestamp": timestamp,
            "especie": result.get("species", ""),
            "nombre_cientifico": result.get("scientific_name", ""),
            "confianza": result.get("confidence", 0),
            "modo": mode,
            "latitude": lat if lat is not None else "",
            "longitude": lon if lon is not None else "",
            "estado_conservacion": result.get("conservation_status", ""),
            "accion_inmediata": result.get("immediate_action", ""),
        })
    print(f"💾 Historial guardado en {HISTORIAL_FILE}")


def mostrar_resultado(result, mode="turtle"):
    print("=" * 55)
    print("🐢 WILDLIFE TRACK CLASSIFIER — Resultado")
    print("=" * 55)

    confianza = result.get("confidence", 0)
    emoji = "🟢" if confianza >= 75 else "🟡" if confianza >= 50 else "🔴"

    print(f"\n📋 Especie: {result.get('species', 'N/A')}")
    print(f"🔬 Nombre científico: {result.get('scientific_name', 'N/A')}")
    print(f"{emoji} Confianza: {confianza}%")

    if mode == "turtle":
        if "measurements" in result:
            m = result["measurements"]
            print(f"\n📏 Medidas estimadas:")
            print(f"   Ancho del rastro: {m.get('track_width_cm', 'N/A')} cm")
            print(f"   Longitud de zancada: {m.get('stride_length_cm', 'N/A')} cm")
            print(f"   Patrón: {m.get('pattern', 'N/A')}")

        if result.get("animal_size_estimate"):
            print(f"\n📐 Tamaño estimado del animal:")
            print(f"   {result['animal_size_estimate']}")

        if result.get("track_condition"):
            print(f"\n🏖️  Condición del rastro:")
            print(f"   {result['track_condition']}")

        if result.get("estimated_nesting_time"):
            print(f"\n🕐 Hora estimada de anidado:")
            print(f"   {result['estimated_nesting_time']}")

    if "conservation_status" in result:
        print(f"\n⚠️  Estado de conservación: {result.get('conservation_status', 'N/A')}")

    if "key_features" in result:
        print(f"\n🔍 Características clave:")
        for f in result.get("key_features", []):
            print(f"   • {f}")

    print(f"\n📝 Notas de campo:")
    print(f"   {result.get('field_notes', 'N/A')}")

    if result.get("immediate_action"):
        print(f"\n🚨 ACCIÓN INMEDIATA:")
        print(f"   {result['immediate_action']}")

    print(f"\n✅ Recomendación:")
    print(f"   {result.get('recommendation', 'N/A')}")
    print("=" * 55)

    output_file = "resultado_clasificacion.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Resultado guardado en {output_file}")

def modo_interactivo():
    """Menú interactivo en terminal."""
    print("\n" + "=" * 55)
    print("🐢 WILDLIFE TRACK CLASSIFIER")
    print("   Herramienta de identificación de rastros con IA")
    print("=" * 55)

    while True:
        print("\n¿Qué quieres hacer?")
        print("  [1] Clasificar una imagen")
        print("  [2] Ver historial de clasificaciones")
        print("  [3] Salir")
        opcion = input("\n→ Elige una opción: ").strip()

        if opcion == "1":
            image_path = input("→ Ruta de la imagen: ").strip()
            print("\n→ Modo:")
            print("  [1] Tortugas marinas (principal)")
            print("  [2] Fauna general (secundario)")
            modo_opcion = input("→ Elige modo [1]: ").strip()
            mode = "wildlife" if modo_opcion == "2" else "turtle"

            try:
                result = clasificar(image_path, mode)
                mostrar_resultado(result, mode)
                guardar_historial(image_path, result, mode)
            except Exception as e:
                print(f"❌ Error: {e}")

        elif opcion == "2":
            if not os.path.exists(HISTORIAL_FILE):
                print("📭 Sin clasificaciones previas.")
            else:
                print(f"\n📊 Historial — {HISTORIAL_FILE}\n")
                with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                    print(f.read())

        elif opcion == "3":
            print("\n👋 Hasta luego.\n")
            break
        else:
            print("❌ Opción no válida.")

def main():
    parser = argparse.ArgumentParser(
        description="🐢 Wildlife Track Classifier"
    )
    parser.add_argument("--image", help="Ruta a la imagen del rastro")
    parser.add_argument("--mode", choices=["turtle", "wildlife"], default="turtle")
    args = parser.parse_args()

    if args.image:
        try:
            result = clasificar(args.image, args.mode)
            mostrar_resultado(result, args.mode)
            guardar_historial(args.image, result, args.mode)
        except json.JSONDecodeError:
            print("❌ Error: respuesta no es JSON válido")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
    else:
        modo_interactivo()

if __name__ == "__main__":
    main()
