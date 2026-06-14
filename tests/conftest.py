"""Shared fixtures for tests."""
import pytest


@pytest.fixture
def sample_question():
    return "What are our top 5 products by revenue?"


@pytest.fixture
def sample_results():
    return [
        {"product": "Laptop Pro", "revenue": 25000.50},
        {"product": "Smartphone X", "revenue": 18000.00},
        {"product": "Wireless Headphones", "revenue": 7500.75},
        {"product": "Running Shoes", "revenue": 5200.00},
        {"product": "Yoga Mat Premium", "revenue": 3200.00},
    ]
