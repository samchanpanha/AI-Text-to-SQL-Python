"""
Sample e-commerce data for development and testing.
Run: python -m app.database.sample_data
"""

from datetime import datetime, timedelta
import random

from app.database.connection import SessionLocal, engine, Base
from app.database.models import Customer, Category, Product, Order, OrderItem


def create_tables():
    Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()

    try:
        if db.query(Customer).count() > 0:
            print("Database already seeded. Skipping.")
            return

        # Categories
        categories = [
            Category(name="Electronics", description="Gadgets and electronic devices"),
            Category(name="Clothing", description="Apparel and accessories"),
            Category(name="Home & Garden", description="Home improvement and garden supplies"),
            Category(name="Books", description="Books and magazines"),
            Category(name="Sports", description="Sports equipment and gear"),
        ]
        db.add_all(categories)
        db.commit()
        for c in categories:
            db.refresh(c)

        # Products
        products_data = [
            ("Smartphone X", 799.99, 150, 1),
            ("Laptop Pro", 1299.99, 75, 1),
            ("Wireless Headphones", 149.99, 200, 1),
            ("T-Shirt Cotton", 29.99, 500, 2),
            ("Denim Jeans", 79.99, 300, 2),
            ("Winter Jacket", 199.99, 100, 2),
            ("Garden Hose 50ft", 34.99, 250, 3),
            ("Indoor Plant Set", 49.99, 180, 3),
            ("Cookbook: World Recipes", 24.99, 400, 4),
            ("Fiction Bestseller", 19.99, 350, 4),
            ("Yoga Mat Premium", 39.99, 220, 5),
            ("Running Shoes", 129.99, 160, 5),
        ]
        products = []
        for name, price, stock, cat_id in products_data:
            products.append(Product(name=name, price=price, stock_qty=stock, category_id=cat_id))
        db.add_all(products)
        db.commit()
        for p in products:
            db.refresh(p)

        # Customers
        customers_data = [
            ("Alice Johnson", "alice@example.com", "555-0101", "New York"),
            ("Bob Smith", "bob@example.com", "555-0102", "Los Angeles"),
            ("Charlie Brown", "charlie@example.com", "555-0103", "Chicago"),
            ("Diana Prince", "diana@example.com", "555-0104", "Houston"),
            ("Eve Adams", "eve@example.com", "555-0105", "Phoenix"),
            ("Frank Castle", "frank@example.com", "555-0106", "Philadelphia"),
            ("Grace Hopper", "grace@example.com", "555-0107", "San Antonio"),
            ("Henry Ford", "henry@example.com", "555-0108", "San Diego"),
        ]
        customers = []
        for name, email, phone, city in customers_data:
            customers.append(Customer(name=name, email=email, phone=phone, city=city))
        db.add_all(customers)
        db.commit()
        for c in customers:
            db.refresh(c)

        # Orders (last 90 days)
        statuses = ["pending", "shipped", "delivered", "cancelled"]
        for _ in range(50):
            customer = random.choice(customers)
            days_ago = random.randint(0, 90)
            order_date = datetime.utcnow() - timedelta(days=days_ago)
            status = random.choice(statuses)
            order = Order(customer_id=customer.id, order_date=order_date, status=status)
            db.add(order)
            db.flush()

            # 1-5 items per order
            total = 0.0
            for _ in range(random.randint(1, 5)):
                product = random.choice(products)
                qty = random.randint(1, 3)
                item = OrderItem(order_id=order.id, product_id=product.id, qty=qty, unit_price=product.price)
                db.add(item)
                total += qty * product.price

            order.total = round(total, 2)

        db.commit()
        print("Sample data seeded successfully!")
        print(f"  Categories: {len(categories)}")
        print(f"  Products: {len(products)}")
        print(f"  Customers: {len(customers)}")
        print(f"  Orders: 50")

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    create_tables()
    seed()
