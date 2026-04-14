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

## 🎯 Cómo Usar

1. Descarga el código:
```bash
git clone https://github.com/toshi-taz/track-classifier.git
cd track-classifier
```

2. Instala dependencias:
```bash
pip install -r requirements.txt
```

3. Configura tu API key:
```bash
export GEMINI_API_KEY="tu_api_key_aqui"
```

4. Ejecuta:
```bash
python app.py
```

5. Abre en navegador:
http://localhost:5000

## 🌍 Para Qué Sirve

- 🐢 Clasificación automática de rastros marinos (Xcaret, Reserva Pacuare)
- 🦁 Identificación de fauna terrestre (Rewilding Argentina)
- 📸 Análisis de fotos de cámaras trampa
- 📊 Historial georreferenciado de observaciones

## 🔄 Stack

| Parte | Tecnología |
|-------|------------|
| Backend | Python / Flask |
| IA | Google Gemini Vision API |
| Frontend | HTML/CSS/Bootstrap |
| Datos | Pandas + CSV |
| Deploy | Render |

## 📝 Roadmap

- [x] Clasificación básica
- [x] Historial en CSV
- [x] API REST
- [ ] GPS + Mapas (en desarrollo)
- [ ] Base de datos SQL
- [ ] Autenticación multi-usuario

## 🤝 Contribuciones

¿Trabajas en monitoreo de especies o tecnología para conservación? ¡Contribuciones bienvenidas!

Desarrollado para equipos de conservación en Mesoamérica y Patagonia.


