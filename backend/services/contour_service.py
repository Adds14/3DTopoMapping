"""
Contour Service — Generates transparent contour line overlays from elevation data.

Takes a numpy elevation array and renders topographic contour lines
using Matplotlib on a transparent RGBA canvas, suitable for overlaying
on basemap images.
"""

import io
import numpy as np
import matplotlib
import matplotlib.patheffects as patheffects

matplotlib.use("Agg")  # Non-interactive backend for headless servers
import matplotlib.pyplot as plt
from PIL import Image


def compute_elevation_parameters(elevation_array: np.ndarray, num_levels: int = 15):
    """
    Compute canonical min, max, and contour levels for the elevation grid.
    Returns (masked_elevation, vmin, vmax, levels).
    """
    masked = np.ma.masked_invalid(elevation_array)
    if masked.count() == 0:
        return masked, 0.0, 100.0, np.linspace(0, 100, num_levels)

    vmin = float(np.nanmin(masked))
    vmax = float(np.nanmax(masked))
    
    if vmin == vmax:
        vmax += 1.0

    levels = np.linspace(vmin, vmax, num_levels)
    return masked, vmin, vmax, levels


def _get_web_mercator_coords(lats: np.ndarray, lons: np.ndarray):
    """
    Convert 1D arrays of latitudes and longitudes to 2D meshgrids 
    of Web Mercator (EPSG:3857) X and Y coordinates (in radians).
    """
    import math
    X_merc = np.radians(lons)
    # math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    Y_merc = np.array([math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) for lat in lats])
    return np.meshgrid(X_merc, Y_merc)


def generate_contour_overlay(
    masked_elevation: np.ma.MaskedArray,
    levels: np.ndarray,
    lats: np.ndarray,
    lons: np.ndarray,
    figsize: tuple[float, float] = (12, 12),
    label_fontsize: int = 11,
    show_filled: bool = True,
    show_contours: bool = True,
    show_labels: bool = True,
    color_opacity: float = 0.35,
    line_color: str = "#4a2e15",  # Dark topo brown
    line_width: float = 2.0,
) -> Image.Image:
    """
    Generate a transparent contour line overlay in Web Mercator projection.
    """
    if masked_elevation.count() == 0:
        return Image.new("RGBA", (int(figsize[0] * 100), int(figsize[1] * 100)), (0, 0, 0, 0))

    X_merc, Y_merc = _get_web_mercator_coords(lats, lons)

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    # Plot contours using Web Mercator coordinates
    if show_filled:
        filled = ax.contourf(
            X_merc, Y_merc, masked_elevation,
            levels=levels,
            cmap="terrain",
            alpha=color_opacity,
            extend="both",
        )

    if show_contours:
        contours = ax.contour(
            X_merc, Y_merc, masked_elevation,
            levels=levels,
            colors=line_color,
            linewidths=line_width,
            alpha=0.9,
        )

        if show_labels:
            # Only draw labels on major contours (every 3rd level)
            major_levels = levels[::3]
            labels = ax.clabel(
                contours,
                levels=major_levels,
                inline=True,
                fontsize=label_fontsize,
                fmt="%1.0f m",
                colors=line_color,
            )
            
            for t in labels:
                t.set_path_effects([patheffects.withStroke(linewidth=3, foreground='white')])

    # We must explicitly set the bounds to exactly match the Web Mercator bounding box of the area.
    # Because basemap_service.py fetched and cropped tiles based on the exact same [west, east, north, south]
    # We will get the mercator coordinates of the corners and set xlim/ylim to them.
    import math
    west_merc = math.radians(lons.min())
    east_merc = math.radians(lons.max())
    # South and North mercator bounds
    south_merc = math.log(math.tan(math.pi / 4 + math.radians(lats.min()) / 2))
    north_merc = math.log(math.tan(math.pi / 4 + math.radians(lats.max()) / 2))
    
    ax.set_xlim(west_merc, east_merc)
    ax.set_ylim(south_merc, north_merc)

    ax.set_axis_off()
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Render to RGBA buffer
    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="png",
        dpi=100,
        bbox_inches="tight",
        pad_inches=0,
        transparent=True,
    )
    plt.close(fig)
    buf.seek(0)

    return Image.open(buf).convert("RGBA")


def generate_colorbar_legend(
    vmin: float,
    vmax: float,
    figsize: tuple[float, float] = (8, 1),
) -> Image.Image:
    """
    Generate a standalone horizontal color legend for the elevation data.
    """
    if vmin == vmax:
        vmax += 1

    fig, ax = plt.subplots(figsize=figsize)

    # Create a gradient image for the colorbar
    gradient = np.linspace(vmin, vmax, 256)
    gradient = np.vstack((gradient, gradient))

    ax.imshow(gradient, aspect='auto', cmap='terrain', extent=[vmin, vmax, 0, 1])
    ax.set_yticks([])
    ax.set_xlabel('Elevation (Meters)', fontsize=12, fontweight='bold')
    ax.tick_params(labelsize=10)

    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    return Image.open(buf).convert("RGB")

def generate_contour_geojson(
    masked_elevation: np.ma.MaskedArray,
    levels: np.ndarray,
    lats: np.ndarray,
    lons: np.ndarray,
    show_contours: bool = True,
) -> dict:
    """
    Generate GeoJSON vector contours from elevation data.
    """
    if masked_elevation.count() == 0 or not show_contours:
        return {"type": "FeatureCollection", "features": []}

    X, Y = np.meshgrid(lons, lats)

    fig, ax = plt.subplots()
    contours = ax.contour(X, Y, masked_elevation, levels=levels)

    features = []
    # Identify major levels (every 3rd level)
    major_levels = set(levels[::3])
    
    # contours.allsegs is a list of levels, each level is a list of segments (Nx2 arrays)
    for level, segments in zip(contours.levels, contours.allsegs):
        is_major = level in major_levels
        for segment in segments:
            if len(segment) > 1:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": segment.tolist()
                    },
                    "properties": {
                        "elevation": float(level),
                        "is_major": is_major,
                    }
                })
    
    plt.close(fig)

    return {
        "type": "FeatureCollection",
        "features": features
    }

def generate_filled_contour_base64(
    masked_elevation: np.ma.MaskedArray,
    levels: np.ndarray,
    lats: np.ndarray,
    lons: np.ndarray,
    vmin: float,
    vmax: float,
    color_opacity: float = 0.35,
) -> str:
    """
    Generate a base64 encoded PNG of the filled contour gradient.
    """
    import base64
    if masked_elevation.count() == 0:
        return ""

    X, Y = np.meshgrid(lons, lats)

    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    ax.contourf(
        X, Y, masked_elevation,
        levels=levels,
        cmap="terrain",
        alpha=color_opacity,
        extend="both",
        vmin=vmin,
        vmax=vmax,
    )

    ax.set_axis_off()
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="png",
        dpi=150,
        bbox_inches="tight",
        pad_inches=0,
        transparent=True,
    )
    plt.close(fig)
    
    return base64.b64encode(buf.getvalue()).decode('utf-8')
