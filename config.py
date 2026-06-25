SITES = {
    "chile": {
        "name": "(ALMA region)",
        "path": r"C:\Users\2021n\Downloads\era5_wind_data_analysis\data\raw\chile\chile_*.nc",
        "lat": -23.029,
        "lon": -67.755
    },

    "cerro_toco": {
        "name": "Cerro Toco",
        "path": r"C:\Users\2021n\Downloads\era5_wind_data_analysis\data\raw\chile\chile_*.nc",
        "lat": -22.94,
        "lon": -67.78
    },
    "hanle": {
        "name": "Hanle",
        "path": r"C:\Users\2021n\Downloads\era5_wind_data_analysis\data\raw\HN Data Monthly\india_*.nc",
        "lat": 32.779,
        "lon": 78.964
    },

    "nurbula": {
        "name": "Nurbula Top",
        "path": r"C:\Users\2021n\Downloads\era5_wind_data_analysis\data\raw\HN Data Monthly\india_*.nc",
        "lat": 32.804,
        "lon": 78.396
    }
}

VARIABLES = {
    "u": "u10",
    "v": "v10",
    "gust": "i10fg"   # or whatever ERA5 uses in your dataset
}

TIME_DIM = "valid_time"

PERCENTILES = [50, 90, 95, 99]

BASE_DIR = r"C:\Users\2021n\Downloads\era5_wind_data_analysis"

DATA_DIR = BASE_DIR + r"\data\raw"
OUTPUT_DIR = BASE_DIR + r"\outputs"

CHILE_DIR = DATA_DIR + r"\chile"
INDIA_DIR = DATA_DIR + r"\HN Data Monthly"

