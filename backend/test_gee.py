"""Quick test script to verify GEE connection."""
import ee
from config import settings

print("Testing GEE connection...")
print(f"  Service Account: {settings.GEE_SERVICE_ACCOUNT_EMAIL}")
print(f"  Key File: {settings.gee_key_absolute_path}")
print(f"  Project ID: {settings.GEE_PROJECT_ID}")

creds = ee.ServiceAccountCredentials(
    settings.GEE_SERVICE_ACCOUNT_EMAIL,
    settings.gee_key_absolute_path,
)
ee.Initialize(credentials=creds, project=settings.GEE_PROJECT_ID)
print("\n✅ Earth Engine initialized successfully!")

# Quick test: get SRTM info
info = ee.Image("USGS/SRTMGL1_003").getInfo()
print(f"✅ SRTM dataset type: {info['type']}")
print("\nAll systems go! You can now run the server.")
