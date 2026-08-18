# 3D TopoMapping

Generate professional topographic map PDFs from SRTM elevation data. Enter two coordinate points (forming opposite corners of the area you want mapped), and get a downloadable A4 landscape PDF with three map views — Satellite, Terrain, and Streets.

## Features

- **Automated Bounding Box:** Simply enter any two opposite corner points. The backend automatically computes the exact bounding box.
- **Advanced PDF Reporting:** Each map includes a **Dynamic Scale Bar**, **North Arrow**, **Coordinate Graticules (Grid lines)**, and an **Elevation Color Legend**.
- **High-Resolution Overlays:** Precise topographic contour lines dynamically drawn based on 30m NASA SRTM elevation data.
- **Rich Labels:** CartoDB Voyager POI labels overlaid on all map views for street and landmark clarity.

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
  "lat1": 18.5912,
  "lon1": 73.8173,
  "lat2": 18.5903,
  "lon2": 73.8163
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
