from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

DATASET = "martj42/international-football-results-from-1872-to-2017"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def refresh() -> None:
    api = KaggleApi()
    api.authenticate()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    api.dataset_download_files(DATASET, path=str(RAW_DIR), unzip=True, force=True)


if __name__ == "__main__":
    refresh()
    print("Data refreshed from Kaggle.")
