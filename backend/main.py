"""
3D TopoMapping — FastAPI Backend

Main application that orchestrates the full pipeline:
  1. Accept bounding box coordinates from the frontend
  2. Pull SRTM elevation data from Google Earth Engine
  3. Fetch basemap tiles from free providers (Esri, OpenTopoMap, OSM)
  4. Generate contour line overlays with Matplotlib
  5. Composite contours onto basemaps with Pillow
  6. Generate an A4 Landscape PDF with FPDF2
  7. Return the PDF for download
"""
#py -m uvicorn main:app --reload --port 8000
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import ee
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from config import settings
from services.gee_service import get_elevation_data
from services.basemap_service import fetch_all_basemaps
from services.contour_service import generate_contour_overlay
from services.overlay_service import create_composited_maps
from services.pdf_service import generate_pdf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Lifespan: Initialize GEE once at startup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize Google Earth Engine on startup using service account credentials."""
    try:
        credentials = ee.ServiceAccountCredentials(
            settings.GEE_SERVICE_ACCOUNT_EMAIL,
            settings.gee_key_absolute_path,
        )
        ee.Initialize(credentials=credentials)
        logger.info("✅ Google Earth Engine initialized successfully.")
        app.state.gee_ready = True
    except Exception as e:
        logger.error(f"❌ GEE Initialization failed: {e}")
        logger.warning("⚠️  Server will start but map generation will fail until GEE permissions are fixed.")
        app.state.gee_ready = False
        app.state.gee_error = str(e)
    yield
    logger.info("Shutting down 3D TopoMapping server.")


# --- FastAPI App ---
app = FastAPI(
    title="3D TopoMapping",
    description="Generate topographic map PDFs from SRTM elevation data",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request Model ---
class BoundingBoxRequest(BaseModel):
    """Bounding box defined by four coordinates."""

    north: float
    south: float
    east: float
    west: float

    @field_validator("north", "south")
    @classmethod
    def validate_latitude(cls, v, info):
        if not -90 <= v <= 90:
            raise ValueError(f"Latitude must be between -90 and 90, got {v}")
        return v

    @field_validator("east", "west")
    @classmethod
    def validate_longitude(cls, v, info):
        if not -180 <= v <= 180:
            raise ValueError(f"Longitude must be between -180 and 180, got {v}")
        return v

    def model_post_init(self, __context):
        if self.north <= self.south:
            raise ValueError(
                f"North ({self.north}) must be greater than South ({self.south})"
            )


# --- Main Endpoint ---
# Using standard `def` so FastAPI offloads to threadpool (GEE calls are blocking)
@app.post("/api/generate")
def generate_topographic_pdf(request: BoundingBoxRequest):
    """
    Generate a topographic map PDF for the given bounding box.

    Pipeline:
      1. Extract SRTM elevation data from GEE
      2. Fetch satellite, terrain, and streets basemaps
      3. Generate contour line overlay
      4. Composite contours onto each basemap
      5. Generate A4 landscape PDF
      6. Return as downloadable PDF
    """
    logger.info(
        f"📍 Generating topo map for N={request.north}, S={request.south}, "
        f"E={request.east}, W={request.west}"
    )

    # Check if GEE is ready
    if not getattr(app.state, "gee_ready", False):
        gee_err = getattr(app.state, "gee_error", "Unknown error")
        raise HTTPException(
            status_code=503,
            detail=f"Google Earth Engine is not initialized. Fix the GEE permissions and restart the server. Error: {gee_err}",
        )

    try:
        # Step 1: Get elevation data from GEE
        logger.info("🌍 Step 1/5: Fetching SRTM elevation data from GEE...")
        elevation_data = get_elevation_data(
            north=request.north,
            south=request.south,
            east=request.east,
            west=request.west,
        )
        logger.info(f"   ✓ Elevation data shape: {elevation_data.shape}")

        # Step 2: Fetch basemap images
        logger.info("🗺️  Step 2/5: Fetching basemap tiles...")
        basemaps = fetch_all_basemaps(
            north=request.north,
            south=request.south,
            east=request.east,
            west=request.west,
        )
        logger.info(f"   ✓ Fetched {len(basemaps)} basemaps")

        # Step 3: Generate contour overlay
        logger.info("📊 Step 3/5: Generating contour overlay...")
        # Get aspect ratio and pixel dimensions from the satellite map to match contours perfectly
        target_size = basemaps["satellite"].size
        # Matplotlib figsize is in inches (default DPI is 100, so divide by 100)
        target_figsize = (target_size[0] / 100.0, target_size[1] / 100.0)
        contour_overlay = generate_contour_overlay(elevation_data, figsize=target_figsize)
        logger.info(f"   ✓ Contour overlay size: {contour_overlay.size}")

        # Step 4: Composite contours onto basemaps
        logger.info("🎨 Step 4/5: Compositing contours onto basemaps...")
        composited_maps = create_composited_maps(basemaps, contour_overlay)
        logger.info("   ✓ All maps composited")

        # Step 5: Generate PDF with features
        logger.info("📄 Step 5/5: Generating PDF with advanced features...")
        
        # Generate color legend
        from services.contour_service import generate_colorbar_legend
        color_legend_img = generate_colorbar_legend(elevation_data)
        
        pdf_buffer = generate_pdf(
            satellite_img=composited_maps["satellite"],
            terrain_img=composited_maps["terrain"],
            streets_img=composited_maps["streets"],
            bbox_info={
                "north": request.north,
                "south": request.south,
                "east": request.east,
                "west": request.west,
            },
            color_legend_img=color_legend_img
        )
        logger.info("   ✓ PDF generated successfully!")

        # Return PDF as downloadable response
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=topographic_map.pdf"
            },
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while generating the topographic map: {str(e)}",
        )


# --- Health check ---
@app.get("/api/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "3D TopoMapping"}


# --- Serve frontend static files ---
# This must be LAST so it doesn't override API routes
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
