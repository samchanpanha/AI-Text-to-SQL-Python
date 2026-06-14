"""Test Excel report generation and formatting."""

import os
import tempfile


class TestFormatter:
    def test_get_column_format_currency(self):
        from app.reports.formatter import get_column_format
        fmt = get_column_format("unit_price")
        assert fmt["number_format"] == "#,##0.00"
        assert fmt["force_text"] is False

    def test_get_column_format_text(self):
        from app.reports.formatter import get_column_format
        fmt = get_column_format("phone_number")
        assert fmt["force_text"] is True

    def test_get_column_format_integer(self):
        from app.reports.formatter import get_column_format
        fmt = get_column_format("stock_qty")
        assert fmt["number_format"] == "#,##0"

    def test_get_column_format_rate(self):
        from app.reports.formatter import get_column_format
        fmt = get_column_format("tax_rate")
        assert fmt["number_format"] == "#,##0.0000"


class TestGenerator:
    def test_excel_generation(self):
        from app.reports.generator import _write_excel
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = _write_excel(
                columns=["Name", "Price", "Qty"],
                rows=[["Product A", 10.50, 5], ["Product B", 25.00, 3]],
                output_dir=tmpdir,
            )
            assert os.path.exists(filepath)
            assert filepath.endswith(".xlsx")
            assert os.path.getsize(filepath) > 0
