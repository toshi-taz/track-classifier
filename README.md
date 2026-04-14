# Wildlife Track Classifier 🐢🔍

**🟢 Live en [https://track-classifier.onrender.com](https://track-classifier.onrender.com)**

> Herramienta de IA de campo para identificación de rastros de tortugas marinas y fauna silvestre.  
> Desarrollada para programas de monitoreo de playas — FFCM Campamentos Tortugueros, México.

---

<!-- Screenshot: reemplaza esta línea con tu imagen cuando hagas deploy
![UI Screenshot](docs/screenshot.png)
-->

---

CLI tool for identifying wildlife tracks and signs from photos using Gemini Vision AI.

Developed as a field tool for sea turtle monitoring programs.

## Features
- Identify sea turtle species from beach track photos
- Estimate track measurements (width, stride length, pattern)
- Conservation status and field recommendations
- General wildlife mode for any animal tracks
- Results saved as JSON for data pipeline integration
- Web UI with drag-and-drop image upload and classification history

## Supported Species
- *Chelonia mydas* — Green sea turtle
- *Caretta caretta* — Loggerhead sea turtle  
- *Eretmochelys imbricata* — Hawksbill sea turtle
- *Dermochelys coriacea* — Leatherback sea turtle

## Setup
```bash
git clone https://github.com/toshi-taz/track-classifier.git
cd track-classifier
pip install -r requirements.txt
```

Create `.env` file:
```
GEMINI_API_KEY=your_api_key_here
```

## Usage

### Web app (Flask)
```bash
python app.py
# → http://localhost:5000
```

### CLI
```bash
# Sea turtle track identification
python classifier.py --image photo.jpg --mode turtle

# General wildlife track
python classifier.py --image photo.jpg --mode wildlife

# Interactive menu
python classifier.py
```

## Example Output
```json
{
  "species": "Green sea turtle",
  "scientific_name": "Chelonia mydas",
  "confidence": 95,
  "measurements": {
    "track_width_cm": 100,
    "stride_length_cm": 90,
    "pattern": "simultaneous"
  },
  "conservation_status": "Endangered",
  "key_features": ["Simultaneous front flipper impressions", "..."],
  "field_notes": "...",
  "recommendation": "..."
}
```

## Deploy

### Render.com (included `render.yaml`)
1. Fork or push this repo to GitHub
2. Create a new **Web Service** on [render.com](https://render.com) and connect the repo
3. Render auto-detects `render.yaml` — no manual config needed
4. Set the required environment variable in the Render dashboard:

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Google AI Studio API key ([get one here](https://aistudio.google.com/app/apikey)) |

5. Deploy — build command runs `pip install -r requirements.txt`, start command runs `gunicorn app:app`

> **Note:** The free Render tier spins down after 15 min of inactivity. First request after sleep takes ~30 s.

### Local / self-hosted
```bash
gunicorn app:app --bind 0.0.0.0:5000
```

## Field Application
Designed for use in sea turtle nesting beach monitoring programs such as FFCM Campamentos Tortugueros (Mexico).

## Author
Alexander Toshiro Bataz López  
Ingeniería en Sistemas Energéticos y Redes Inteligentes — UPIEM–IPN  
Conservation Technology | Wildlife Telemetry | IoT Sensor Networks
