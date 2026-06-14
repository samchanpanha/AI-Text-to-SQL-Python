"""
Initialize database: create tables and seed sample data.
Usage: python -m scripts.init_db
"""

from app.database.sample_data import create_tables, seed


def main():
    print("Creating tables...")
    create_tables()
    print("Tables created successfully.")

    print("Seeding sample data...")
    seed()
    print("Database initialization complete.")


if __name__ == "__main__":
    main()
