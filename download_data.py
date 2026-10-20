"""Optional download of the original MRL Eye dataset for re-training."""

from pathlib import Path
import urllib.request


DATA_URL = "https://mrl.cs.vsb.cz/data/eyedataset/mrlEyes_2018_01.zip"
DESTINATION = Path(__file__).resolve().parent / "data" / "mrlEyes_2018_01.zip"


def main():
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    if DESTINATION.exists() and DESTINATION.stat().st_size > 300_000_000:
        print(f"Dữ liệu đã được tải trước đó: {DESTINATION}")
        return
    temp = DESTINATION.with_suffix(".zip.partial")
    print("Đang tải MRL Eye Dataset gốc (~326 MB). Vui lòng đợi...", flush=True)

    def progress(blocks, block_size, size):
        if blocks % 400 == 0 and size > 0:
            print(f"  {min(100, blocks * block_size / size * 100):.0f}%", flush=True)

    try:
        urllib.request.urlretrieve(DATA_URL, temp, reporthook=progress)
        if temp.stat().st_size < 300_000_000:
            raise RuntimeError("Tệp dữ liệu tải về chưa đầy đủ.")
        temp.replace(DESTINATION)
    except Exception:
        if temp.exists():
            temp.unlink()
        raise
    print(f"Đã tải xong: {DESTINATION}")


if __name__ == "__main__":
    main()
