from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json
import argparse
import sys
from PIL import Image
import pathlib

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

from prompts.species import TURTLE_PROMPT, GENERAL_WILDLIFE_PROMPT

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

def mostrar_resultado(result, mode="turtle"):
    print("=" * 55)
    print("🐢 WILDLIFE TRACK CLASSIFIER — Resultado")
    print("=" * 55)

    confianza = result.get("confidence", 0)
    emoji = "🟢" if confianza >= 75 else "🟡" if confianza >= 50 else "🔴"

    print(f"\n📋 Especie: {result.get('species', 'N/A')}")
    print(f"🔬 Nombre científico: {result.get('scientific_name', 'N/A')}")
    print(f"{emoji} Confianza: {confianza}%")

    if mode == "turtle" and "measurements" in result:
        m = result["measurements"]
        print(f"\n📏 Medidas estimadas:")
        print(f"   Ancho del rastro: {m.get('track_width_cm', 'N/A')} cm")
        print(f"   Longitud de zancada: {m.get('stride_length_cm', 'N/A')} cm")
        print(f"   Patrón: {m.get('pattern', 'N/A')}")

    if "conservation_status" in result:
        print(f"\n⚠️  Estado de conservación: {result.get('conservation_status', 'N/A')}")

    if "key_features" in result:
        print(f"\n🔍 Características clave:")
        for f in result.get("key_features", []):
            print(f"   • {f}")

    print(f"\n📝 Notas de campo:")
    print(f"   {result.get('field_notes', 'N/A')}")

    print(f"\n✅ Recomendación:")
    print(f"   {result.get('recommendation', 'N/A')}")
    print("=" * 55)

    output_file = "resultado_clasificacion.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Resultado guardado en {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description="🐢 Wildlife Track Classifier — Identificación de rastros con IA"
    )
    parser.add_argument("--image", required=True, help="Ruta a la imagen del rastro")
    parser.add_argument("--mode", choices=["turtle", "wildlife"], default="turtle",
                        help="Modo de clasificación (default: turtle)")
    args = parser.parse_args()

    try:
        result = clasificar(args.image, args.mode)
        mostrar_resultado(result, args.mode)
    except json.JSONDecodeError:
        print("❌ Error: respuesta no es JSON válido")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()
