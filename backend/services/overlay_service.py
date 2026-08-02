"""
Overlay Service — Composites contour lines onto basemap images.

Uses PIL to alpha-composite transparent contour overlays
onto opaque basemap images, matching dimensions via resize.
"""

from PIL import Image


def overlay_contours(
    basemap: Image.Image,
    contour_overlay: Image.Image,
    opacity: float = 1.0,
) -> Image.Image:
    """
    Overlay transparent contour lines onto a basemap image.

    Args:
        basemap: The base map image (RGB)
        contour_overlay: Contour lines on transparent background (RGBA)
        opacity: Overall opacity of the overlay (0.0 to 1.0)

    Returns:
        Composited PIL Image (RGB)
    """
    # Ensure basemap is RGBA for compositing
    base = basemap.convert("RGBA")

    # Resize contour overlay to match basemap dimensions
    overlay = contour_overlay.resize(base.size, Image.LANCZOS)

    # Apply overall opacity if less than 1.0
    if opacity < 1.0:
        # Reduce alpha channel by the opacity factor
        r, g, b, a = overlay.split()
        a = a.point(lambda x: int(x * opacity))
        overlay = Image.merge("RGBA", (r, g, b, a))

    # Composite the overlay onto the basemap
    composited = Image.alpha_composite(base, overlay)

    # Convert back to RGB for PDF compatibility
    return composited.convert("RGB")


def create_composited_maps(
    basemaps: dict[str, Image.Image],
    contour_overlay: Image.Image,
) -> dict[str, Image.Image]:
    """
    Apply contour overlay to all basemap styles.

    Args:
        basemaps: Dictionary of style_name → basemap PIL Image
        contour_overlay: Transparent contour overlay image

    Returns:
        Dictionary of style_name → composited PIL Image
    """
    composited = {}
    for style_name, basemap in basemaps.items():
        composited[style_name] = overlay_contours(basemap, contour_overlay)
    return composited
