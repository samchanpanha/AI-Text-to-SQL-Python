"""Test schema introspection and formatting."""


class TestSchema:
    def test_format_schema_for_prompt(self):
        from app.database.schema import format_schema_for_prompt
        schemas = {
            "products": {
                "columns": [
                    {"name": "id", "type": "INT", "nullable": False, "default": "", "primary_key": True},
                    {"name": "name", "type": "VARCHAR(255)", "nullable": False, "default": "", "primary_key": False},
                    {"name": "price", "type": "FLOAT", "nullable": True, "default": "", "primary_key": False},
                ],
                "foreign_keys": [],
                "row_count": 100,
            },
        }
        result = format_schema_for_prompt(schemas)
        assert "products" in result
        assert "price" in result
        assert "100 rows" in result

    def test_format_schema_with_fk(self):
        from app.database.schema import format_schema_for_prompt
        schemas = {
            "orders": {
                "columns": [
                    {"name": "id", "type": "INT", "nullable": False, "default": "", "primary_key": True},
                    {"name": "customer_id", "type": "INT", "nullable": False, "default": "", "primary_key": False},
                ],
                "foreign_keys": [
                    {"column": ["customer_id"], "references": "customers.id"},
                ],
                "row_count": 50,
            },
        }
        result = format_schema_for_prompt(schemas)
        assert "FK" in result
        assert "customer_id" in result
