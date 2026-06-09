from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
