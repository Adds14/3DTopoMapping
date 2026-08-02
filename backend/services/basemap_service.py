"""
Basemap Service — Fetches map tiles from free providers and stitches them
into a single image for a given bounding box.

Uses three free tile providers (no API keys required):
  - Satellite: Esri World Imagery
  - Terrain:   OpenTopoMap
  - Streets:   OpenStreetMap

Tiles are fetched at the appropriate zoom level, cropped to the exact
bounding box, and returned as PIL Images.
"""

import io
import math
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from PIL import Image

# --- Tile provider URLs ---
TILE_PROVIDERS = {
    "satellite": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "labels_url": "https://a.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}.png",
        "label": "Satellite View",
        "attribution": "© Esri | Labels © CartoDB",
        "max_zoom": 19,
    },
    "terrain": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        "labels_url": "https://a.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}.png",
        "label": "Terrain (Topo) View",
        "attribution": "© Esri | Labels © CartoDB",
        "max_zoom": 16,
    },
    "streets": {
        "url": "https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
        "labels_url": None,
        "label": "Streets View",
        "attribution": "© CartoDB",
        "max_zoom": 20,
    },
}

# Standard web mercator tile size
TILE_SIZE = 256

# User-Agent header required by OSM tile usage policy
HEADERS = {
    "User-Agent": "3DTopoMappingApp/1.0 (contact: info@example.com) Mozilla/5.0"
}


def _lat_lon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    """Convert lat/lon to tile coordinates at a given zoom level."""
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    # Clamp to valid range
    x = max(0, min(x, n - 1))
    y = max(0, min(y, n - 1))
    return x, y


def _tile_to_lat_lon(x: int, y: int, zoom: int) -> tuple[float, float]:
    """Convert tile coordinates back to lat/lon (top-left corner of tile)."""
    n = 2 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon


def _calculate_zoom(north: float, south: float, east: float, west: float, target_size: int = 1280) -> int:
    """
    Calculate the best zoom level to get roughly target_size pixels
    for the bounding box.
    """
    for zoom in range(18, 0, -1):
        x_min, _ = _lat_lon_to_tile(north, west, zoom)[0], None
        x_max, _ = _lat_lon_to_tile(south, east, zoom)[0], None

        x1, y1 = _lat_lon_to_tile(north, west, zoom)
        x2, y2 = _lat_lon_to_tile(south, east, zoom)

        width_tiles = abs(x2 - x1) + 1
        height_tiles = abs(y2 - y1) + 1

        pixel_width = width_tiles * TILE_SIZE
        pixel_height = height_tiles * TILE_SIZE

        if pixel_width <= target_size * 3 and pixel_height <= target_size * 3:
            return zoom

    return 10  # Fallback


def _fetch_single_tile(url: str) -> bytes | None:
    """Fetch a single tile image, returning raw bytes or None on failure."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return response.content
    except requests.RequestException:
        pass
    return None


def fetch_basemap(
    north: float,
    south: float,
    east: float,
    west: float,
    style: str = "satellite",
    output_size: int = 1280,
) -> Image.Image:
    """
    Fetch a basemap image for the given bounding box from free tile providers.

    Args:
        north: Northern latitude
        south: Southern latitude
        east: Eastern longitude
        west: Western longitude
        style: One of 'satellite', 'terrain', 'streets'
        output_size: Target output image size in pixels

    Returns:
        PIL Image of the basemap cropped to the exact bounding box
    """
    provider = TILE_PROVIDERS[style]
    url_template = provider["url"]

    # Find the best zoom level
    zoom = _calculate_zoom(north, south, east, west, output_size)
    if "max_zoom" in provider:
        zoom = min(zoom, provider["max_zoom"])

    # Get tile ranges
    x_min, y_min = _lat_lon_to_tile(north, west, zoom)
    x_max, y_max = _lat_lon_to_tile(south, east, zoom)

    # Ensure min <= max
    if x_min > x_max:
        x_min, x_max = x_max, x_min
    if y_min > y_max:
        y_min, y_max = y_max, y_min

    width_tiles = x_max - x_min + 1
    height_tiles = y_max - y_min + 1

    # Create a blank canvas for all tiles
    canvas = Image.new("RGBA", (width_tiles * TILE_SIZE, height_tiles * TILE_SIZE), (200, 200, 200, 255))

    def _fetch_and_paste(urls_with_coords):
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_map = {
                executor.submit(_fetch_single_tile, url): (tx, ty)
                for tx, ty, url in urls_with_coords
            }
            for future in as_completed(future_map):
                tx, ty = future_map[future]
                tile_data = future.result()
                if tile_data:
                    try:
                        tile_img = Image.open(io.BytesIO(tile_data)).convert("RGBA")
                        paste_x = (tx - x_min) * TILE_SIZE
                        paste_y = (ty - y_min) * TILE_SIZE
                        canvas.paste(tile_img, (paste_x, paste_y), tile_img)
                    except Exception:
                        pass  # Skip corrupt tiles

    # Build list of base tiles to fetch
    base_jobs = []
    for ty in range(y_min, y_max + 1):
        for tx in range(x_min, x_max + 1):
            url = url_template.format(z=zoom, x=tx, y=ty)
            base_jobs.append((tx, ty, url))

    # Fetch and paste base tiles
    _fetch_and_paste(base_jobs)

    # Fetch and paste label tiles if available
    labels_url_template = provider.get("labels_url")
    if labels_url_template:
        label_jobs = []
        for ty in range(y_min, y_max + 1):
            for tx in range(x_min, x_max + 1):
                url = labels_url_template.format(z=zoom, x=tx, y=ty)
                label_jobs.append((tx, ty, url))
        _fetch_and_paste(label_jobs)

    canvas = canvas.convert("RGB")

    # --- Crop to exact bounding box ---
    # Calculate pixel positions of the exact bbox corners within the stitched canvas
    n = 2 ** zoom

    # West edge pixel offset
    west_frac = (west + 180.0) / 360.0 * n
    px_left = (west_frac - x_min) * TILE_SIZE

    # East edge pixel offset
    east_frac = (east + 180.0) / 360.0 * n
    px_right = (east_frac - x_min) * TILE_SIZE

    # North edge pixel offset (top of image)
    north_rad = math.radians(north)
    north_frac = (1.0 - math.log(math.tan(north_rad) + 1.0 / math.cos(north_rad)) / math.pi) / 2.0 * n
    px_top = (north_frac - y_min) * TILE_SIZE

    # South edge pixel offset (bottom of image)
    south_rad = math.radians(south)
    south_frac = (1.0 - math.log(math.tan(south_rad) + 1.0 / math.cos(south_rad)) / math.pi) / 2.0 * n
    px_bottom = (south_frac - y_min) * TILE_SIZE

    # Clamp to canvas bounds
    px_left = max(0, int(px_left))
    px_top = max(0, int(px_top))
    px_right = min(canvas.width, int(px_right))
    px_bottom = min(canvas.height, int(px_bottom))

    if px_right > px_left and px_bottom > px_top:
        canvas = canvas.crop((px_left, px_top, px_right, px_bottom))

    # Scale image so its largest dimension matches output_size, maintaining aspect ratio
    img_w, img_h = canvas.size
    if img_w > 0 and img_h > 0:
        scale = output_size / max(img_w, img_h)
        new_w = max(1, int(img_w * scale))
        new_h = max(1, int(img_h * scale))
        # LANCZOS provides smooth upscaling and downscaling
        canvas = canvas.resize((new_w, new_h), Image.Resampling.LANCZOS)

    return canvas


def fetch_all_basemaps(
    north: float,
    south: float,
    east: float,
    west: float,
    output_size: int = 1280,
) -> dict[str, Image.Image]:
    """
    Fetch all three basemap styles for the given bounding box.

    Returns:
        Dictionary with keys 'satellite', 'terrain', 'streets' mapping to PIL Images
    """
    results = {}
    # Fetch all three styles concurrently using threads
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(fetch_basemap, north, south, east, west, style, output_size): style
            for style in TILE_PROVIDERS
        }
        for future in as_completed(futures):
            style = futures[future]
            try:
                results[style] = future.result()
            except Exception as e:
                # Create a placeholder gray image on failure
                placeholder = Image.new("RGB", (output_size, output_size), (60, 60, 60))
                results[style] = placeholder
                print(f"Warning: Failed to fetch {style} basemap: {e}")

    return results
