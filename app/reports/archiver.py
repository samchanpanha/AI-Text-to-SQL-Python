import os
import time
from zipfile import ZipFile

from config.app import Settings


settings = Settings()


def create_zip(
    files: list[dict],
    task_id: int,
    output_dir: str | None = None,
) -> str:
    """
    Zip multiple files after all are generated.
    Waits for files to exist before archiving — never produces partial zips.
    """
    dir_path = output_dir or settings.REPORT_TEMP_DIR
    os.makedirs(dir_path, exist_ok=True)

    # Verify all files exist before zipping
    for f in files:
        path = f.get("path")
        if path and not os.path.exists(path):
            raise FileNotFoundError(f"File not found before zipping: {path}")

    zip_name = f"report_{task_id}_{int(time.time())}.zip"
    zip_path = os.path.join(dir_path, zip_name)

    with ZipFile(zip_path, "w") as zf:
        for f in files:
            path = f.get("path")
            if path and os.path.exists(path):
                arcname = f.get("name") or os.path.basename(path)
                zf.write(path, arcname=arcname)

    return zip_path
