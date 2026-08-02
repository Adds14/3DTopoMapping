"""
GEE Service — Extracts SRTM elevation data from Google Earth Engine.

Uses ee.Image('USGS/SRTMGL1_003') to fetch 30m resolution elevation data
for a bounding box, returning it as a numpy array.
"""

import io
import ee
import numpy as np
import requests


def get_elevation_data(
    north: float,
    south: float,
    east: float,
    west: float,
    scale: int = 30,
) -> np.ndarray:
    """
    Extract SRTM elevation data for a bounding box from Google Earth Engine.

    Args:
        north: Northern latitude boundary
        south: Southern latitude boundary
        east: Eastern longitude boundary
        west: Western longitude boundary
        scale: Resolution in meters (default 30m for SRTM)

    Returns:
        2D numpy array of elevation values in meters

    Raises:
        RuntimeError: If GEE data download fails
    """
    # Define the bounding box geometry
    bbox = ee.Geometry.BBox(west, south, east, north)

    # Load SRTM elevation data and clip to bounding box
    srtm = ee.Image("USGS/SRTMGL1_003").select("elevation")

    # Get download URL in numpy format
    url = srtm.getDownloadURL(
        {
            "format": "NPY",
            "region": bbox,
            "scale": scale,
            "crs": "EPSG:4326",
        }
    )

    # Download the numpy binary data
    response = requests.get(url, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(
            f"GEE download failed with status {response.status_code}: {response.text}"
        )

    # Parse the numpy array from the response
    raw_array = np.load(io.BytesIO(response.content))

    # NPY format returns structured array with band names as keys
    if raw_array.dtype.names and "elevation" in raw_array.dtype.names:
        elevation_array = raw_array["elevation"]
    else:
        elevation_array = raw_array

    # Replace any no-data values (typically -32768 for SRTM) with NaN
    elevation_array = elevation_array.astype(np.float64)
    elevation_array[elevation_array <= -32768] = np.nan

    return elevation_array
