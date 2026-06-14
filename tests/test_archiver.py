"""Test zip archiving of report files."""

import os
import tempfile


class TestArchiver:
    def test_create_zip(self):
        from app.reports.archiver import create_zip
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = os.path.join(tmpdir, "report1.xlsx")
            file2 = os.path.join(tmpdir, "report2.xlsx")
            with open(file1, "w") as f:
                f.write("test1")
            with open(file2, "w") as f:
                f.write("test2")

            files = [
                {"path": file1, "name": "report1.xlsx"},
                {"path": file2, "name": "report2.xlsx"},
            ]

            zip_path = create_zip(files, task_id=1, output_dir=tmpdir)
            assert os.path.exists(zip_path)
            assert zip_path.endswith(".zip")
            assert os.path.getsize(zip_path) > 0
