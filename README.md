# 3D TopoMapping

A professional, interactive GIS workspace to generate topographic maps and PDFs from NASA SRTM elevation data. Enter two coordinate points (forming opposite corners of the area you want mapped), instantly explore the interactive topographic dashboard, and export a high-quality A4 landscape PDF.

## 🚀 Features

- **Map-First GIS Workspace:** A fully interactive, responsive Leaflet-based map interface featuring custom layer cards, floating control panels, and a sleek dark-glassmorphic UI.
- **Dynamic Topographic Overlay:** Generates 30m resolution vector contour lines and color-coded elevation gradients in real-time, rendered directly on the interactive map.
- **Automated Bounding Box:** Simply enter any two opposite corner points. The backend automatically computes the exact geographic bounding box.
- **Advanced PDF Export:** Generate a downloadable A4 landscape PDF with three map views — Satellite, Terrain, and Streets. Each map includes a **Dynamic Scale Bar**, **North Arrow**, **Coordinate Graticules (Grid lines)**, and an **Elevation Color Legend**.
- **Free & Open Basemaps:** Utilizes Esri World Imagery, OpenTopoMap, and OpenStreetMap (free, no API keys required).

## 🛠 Tech Stack

- **Backend**: FastAPI (Python)
- **Elevation Data**: Google Earth Engine (USGS SRTM 30m)
- **Basemaps**: Esri World Imagery, OpenTopoMap, OpenStreetMap
- **Contour Generation**: Matplotlib & GeoJSON
- **PDF Generation**: Pillow & FPDF2
- **Frontend**: Vanilla HTML/CSS/JS with Leaflet.js

---

## 💻 How to Run

### 1. Prerequisites

- Python 3.10+
- A Google Earth Engine service account with a JSON key file.
- The service account must be [registered for Earth Engine](https://signup.earthengine.google.com/#!/service_accounts).

### 2. Install Dependencies

Open your terminal or command prompt and run:
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment

Create or edit `backend/.env` with your Google Earth Engine (GEE) credentials:

```env
GEE_SERVICE_ACCOUNT_EMAIL=your-sa@your-project.iam.gserviceaccount.com
GEE_KEY_FILE_PATH=credentials/your-key-file.json
GEE_PROJECT_ID=your-gcp-project-id
```

### 4. Start the Server

Run the FastAPI backend server:

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```
*Note: The `--reload` flag ensures the server automatically restarts if you modify any backend files.*

### 5. Open the Application

Once the server is running, navigate to [http://localhost:8000](http://localhost:8000) in your web browser. 

The frontend assets (`index.html`, `style.css`, `script.js`) are served directly by the FastAPI backend, so no separate frontend server is required.

---

## 📡 API Endpoints

### `POST /api/contours`
**Purpose:** Generate GeoJSON vector contours and base64 color shading for the interactive Leaflet map.
**Request Body:**
```json
{
  "lat1": 18.5912, "lon1": 73.8173,
  "lat2": 18.5903, "lon2": 73.8163
}
```
**Response:** JSON object containing `geojson` and `image` (base64).

### `POST /api/generate`
**Purpose:** Generate the high-resolution topographic map PDF export.
**Request Body:** Same as above.
**Response:** PDF file download (`application/pdf`).

### `GET /api/health`
**Purpose:** Health check endpoint to verify backend status.

---

## 📁 Project Structure

```
3dTopoMapping/
├── backend/
│   ├── main.py                  # FastAPI app & Static file serving
│   ├── config.py                # Environment configuration
│   ├── credentials/             # GEE service account key (gitignored)
│   ├── services/
│   │   ├── gee_service.py       # SRTM elevation extraction
│   │   ├── basemap_service.py   # Free tile basemap fetching
│   │   ├── contour_service.py   # Matplotlib contour generation & GeoJSON
│   │   ├── overlay_service.py   # Image compositing
│   │   └── pdf_service.py       # PDF report generation
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── index.html               # GIS workspace layout
│   ├── style.css                # Glassmorphic & responsive styling
│   └── script.js                # Leaflet map logic & API handling
├── .gitignore
└── README.md
```
