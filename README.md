# Wildlife Track Classifier 🐢🔍

CLI tool for identifying wildlife tracks and signs from photos using Gemini Vision AI.

Developed as a field tool for sea turtle monitoring programs.

## Features
- Identify sea turtle species from beach track photos
- Estimate track measurements (width, stride length, pattern)
- Conservation status and field recommendations
- General wildlife mode for any animal tracks
- Results saved as JSON for data pipeline integration

## Supported Species
- *Chelonia mydas* — Green sea turtle
- *Caretta caretta* — Loggerhead sea turtle  
- *Eretmochelys imbricata* — Hawksbill sea turtle
- *Dermochelys coriacea* — Leatherback sea turtle

## Setup
```bash
git clone https://github.com/toshi-taz/track-classifier.git
cd track-classifier
pip install google-genai pillow python-dotenv
```

Create `.env` file:
## Usage
```bash
# Sea turtle track identification
python classifier.py --image photo.jpg --mode turtle

# General wildlife track
python classifier.py --image photo.jpg --mode wildlife
```

## Example Output
## Field Application
Designed for use in sea turtle nesting beach monitoring programs such as FFCM Campamentos Tortugueros (Mexico).

## Author
Alexander Toshiro Bataz López  
Ingeniería en Sistemas Energéticos y Redes Inteligentes — UPIEM–IPN  
Conservation Technology | Wildlife Telemetry | IoT Sensor Networks
