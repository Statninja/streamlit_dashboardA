import subprocess
import sys

try:
    import geopandas as gpd
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "geopandas"])
    import geopandas as gpd
