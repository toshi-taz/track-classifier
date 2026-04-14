# Wildlife Track Classifier 🐢

> Herramienta de IA de campo para identificación de rastros de fauna marina.  
> **Live:** https://track-classifier.onrender.com

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-green)
![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## ¿Qué hace?
Sube una foto de rastros en arena → Gemini Vision identifica la especie,
estima medidas, devuelve estado de conservación y recomendaciones de campo.

## Especies soportadas
| Especie | Nombre científico | Estado |
|---|---|---|
| Tortuga verde | *Chelonia mydas* | Endangered |
| Tortuga caguama | *Caretta caretta* | Vulnerable |
| Tortuga carey | *Eretmochelys imbricata* | Critically Endangered |
| Tortuga laúd | *Dermochelys coriacea* | Vulnerable |

## Stack
- **Backend:** Python 3.14, Flask, Gemini Vision API (gemini-2.5-flash)
- **Frontend:** HTML/CSS/JS vanilla, tipografía Instrument Serif + DM Mono
- **Deploy:** Render.com (free tier)

## Setup local
```bash
git clone https://github.com/toshi-taz/track-classifier
cd track-classifier
pip install -r requirements.txt
# Crea .env con GEMINI_API_KEY=tu_clave
python app.py
```

## Uso CLI (modo original)
```bash
python classifier.py --image foto.jpg --mode turtle
python classifier.py --image foto.jpg --mode wildlife
```

## Autor
Alexander Toshiro Bataz López  
Ingeniería en Sistemas Energéticos y Redes Inteligentes — UPIEM–IPN  
abatazl2300@alumno.ipn.mx

---
*Desarrollado como herramienta de apoyo para FFCM Campamentos Tortugueros*
