import exifread, sys
from fractions import Fraction

def convert_to_degrees(value):
    d = float(value[0].num) / float(value[0].den)
    m = float(value[1].num) / float(value[1].den)
    s = float(value[2].num) / float(value[2].den)
    return d + (m / 60.0) + (s / 3600.0)

def extract_gps(image_path):
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
        gps_latitude = tags.get("GPS GPSLatitude")
        gps_latitude_ref = tags.get("GPS GPSLatitudeRef")
        gps_longitude = tags.get("GPS GPSLongitude")
        gps_longitude_ref = tags.get("GPS GPSLongitudeRef")
        if not (gps_latitude and gps_longitude):
            return None
        lat = convert_to_degrees(gps_latitude.values)
        lon = convert_to_degrees(gps_longitude.values)
        if gps_latitude_ref and gps_latitude_ref.values[0] == "S":
            lat = -lat
        if gps_longitude_ref and gps_longitude_ref.values[0] == "W":
            lon = -lon
        return {"latitude": round(lat, 6), "longitude": round(lon, 6)}
    except Exception as e:
        print(f"⚠️ GPS error: {e}", file=sys.stderr)
        return None
