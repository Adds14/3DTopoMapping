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


def generate_contour_overlay(
    elevation_array: np.ndarray,
    figsize: tuple[int, int] = (12, 12),
    num_levels: int = 15,
    line_color: str = "#4a2e15",  # Dark topo brown
    line_width: float = 2.0,
    label_fontsize: int = 14,
    show_filled: bool = True,
) -> Image.Image:
    """
    Generate a transparent contour line overlay from elevation data.

    Args:
        elevation_array: 2D numpy array of elevation values
        figsize: Figure size in inches (controls resolution)
        num_levels: Number of contour levels to draw
        line_color: Color of contour lines
        line_width: Width of contour lines
        label_fontsize: Font size for contour labels
        show_filled: If True, also render filled contours with transparency

    Returns:
        PIL Image (RGBA) with contour lines on transparent background
    """
    # Handle NaN values for contouring
    masked_elevation = np.ma.masked_invalid(elevation_array)

    if masked_elevation.count() == 0:
        # No valid data — return a fully transparent image
        return Image.new("RGBA", (int(figsize[0] * 100), int(figsize[1] * 100)), (0, 0, 0, 0))

    # Calculate contour levels
    vmin = float(np.nanmin(elevation_array[np.isfinite(elevation_array)]))
    vmax = float(np.nanmax(elevation_array[np.isfinite(elevation_array)]))

    if vmin == vmax:
        # Flat terrain — no contours to draw
        return Image.new("RGBA", (int(figsize[0] * 100), int(figsize[1] * 100)), (0, 0, 0, 0))

    levels = np.linspace(vmin, vmax, num_levels)

    # Create figure with transparent background
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    # Draw filled contours with low opacity (color ramp under the lines)
    if show_filled:
        filled = ax.contourf(
            masked_elevation,
            levels=levels,
            cmap="terrain",
            alpha=0.25,
            extend="both",
        )

    # Draw contour lines
    contours = ax.contour(
        masked_elevation,
        levels=levels,
        colors=line_color,
        linewidths=line_width,
        alpha=0.9,
    )

    # Add elevation labels to contour lines
    labels = ax.clabel(
        contours,
        inline=True,
        fontsize=label_fontsize,
        fmt="%1.0f m",
        colors=line_color,
    )
    
    for t in labels:
        t.set_path_effects([patheffects.withStroke(linewidth=3, foreground='white')])

    # Remove axes, ticks, and padding
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
    elevation_array: np.ndarray,
    figsize: tuple[float, float] = (8, 1),
) -> Image.Image:
    """
    Generate a standalone horizontal color legend for the elevation data.
    """
    masked = np.ma.masked_invalid(elevation_array)
    
    if masked.count() == 0:
        vmin, vmax = 0, 100
    else:
        vmin = float(np.nanmin(masked))
        vmax = float(np.nanmax(masked))
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
