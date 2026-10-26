from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
DATA = PACKAGE / "_data" if (PACKAGE / "_data").is_dir() else PACKAGE.parent
