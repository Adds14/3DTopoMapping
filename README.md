# 3D TopoMapping

Generate professional topographic map PDFs from SRTM elevation data. Enter four coordinates (bounding box), and get a downloadable A4 landscape PDF with three map views — Satellite, Terrain, and Streets — each overlaid with elevation contour lines.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Elevation Data**: Google Earth Engine (USGS SRTM 30m)
- **Basemaps**: Esri World Imagery, OpenTopoMap, OpenStreetMap (free, no API keys)
- **Contour Generation**: Matplotlib
- **Image Compositing**: Pillow
- **PDF Generation**: FPDF2
- **Frontend**: Vanilla HTML/CSS/JS (dark-mode glassmorphic UI)

## Setup

### 1. Prerequisites

- Python 3.10+
- A Google Earth Engine service account with a JSON key file
- The service account must be [registered for Earth Engine](https://signup.earthengine.google.com/#!/service_accounts)

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment

Edit `backend/.env` with your GEE credentials:

```env
GEE_SERVICE_ACCOUNT_EMAIL=your-sa@your-project.iam.gserviceaccount.com
GEE_KEY_FILE_PATH=credentials/your-key-file.json
GEE_PROJECT_ID=your-gcp-project-id
```

### 4. Run the Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Open the App

Navigate to [http://localhost:8000](http://localhost:8000) in your browser.

## API

### `POST /api/generate`

Generate a topographic map PDF.

**Request Body:**
```json
{
  "north": 37.83,
  "south": 37.71,
  "east": -122.35,
  "west": -122.52
}
```

**Response:** PDF file download (`application/pdf`)

### `GET /api/health`

Health check endpoint.

## Project Structure

```
3dTopoMapping/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── config.py                # Environment configuration
│   ├── credentials/             # GEE service account key (gitignored)
│   ├── services/
│   │   ├── gee_service.py       # SRTM elevation extraction
│   │   ├── basemap_service.py   # Free tile basemap fetching
│   │   ├── contour_service.py   # Matplotlib contour generation
│   │   ├── overlay_service.py   # Image compositing
│   │   └── pdf_service.py       # PDF report generation
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── .gitignore
└── README.md
```
