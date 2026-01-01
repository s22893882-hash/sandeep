"""Tests for Items API endpoints."""
import pytest
from fastapi.testclient import TestClient
from httpx import BasicAuth

from app.main import app
from app.models import ItemCreate, ItemUpdate

client = TestClient(app)


class TestItemsAPI:
    """Test suite for Items API."""

    def test_list_items(self):
        """Test listing all items."""
        response = client.get("/items")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # Should have at least the 2 sample items

    def test_list_items_with_pagination(self):
        """Test listing items with pagination."""
        response = client.get("/items?skip=1&limit=1")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_get_item(self):
        """Test getting a specific item."""
        response = client.get("/items/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert "name" in data
        assert "price" in data

    def test_get_item_not_found(self):
        """Test getting a non-existent item."""
        response = client.get("/items/9999")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_create_item(self):
        """Test creating a new item."""
        item_data = {
            "name": "New Item",
            "description": "A newly created item",
            "price": 19.99,
            "quantity": 50,
        }

        response = client.post("/items", json=item_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Item"
        assert data["price"] == 19.99
        assert "id" in data
        assert data["quantity"] == 50

    def test_create_item_invalid_price(self):
        """Test creating an item with invalid price."""
        item_data = {
            "name": "Invalid Item",
            "price": -10.0,
        }

        response = client.post("/items", json=item_data)

        # FastAPI validation should catch this
        assert response.status_code == 422

    def test_create_item_missing_required_fields(self):
        """Test creating an item without required fields."""
        item_data = {
            "description": "Item without name or price",
        }

        response = client.post("/items", json=item_data)

        assert response.status_code == 422

    def test_update_item(self):
        """Test updating an existing item."""
        update_data = {
            "name": "Updated Item Name",
            "price": 29.99,
        }

        response = client.put("/items/1", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Item Name"
        assert data["price"] == 29.99

    def test_update_item_not_found(self):
        """Test updating a non-existent item."""
        update_data = {"name": "Updated Name"}

        response = client.put("/items/9999", json=update_data)

        assert response.status_code == 404

    def test_delete_item(self):
        """Test deleting an item."""
        # First create an item
        create_data = {
            "name": "Item to Delete",
            "price": 9.99,
        }
        create_response = client.post("/items", json=create_data)
        item_id = create_response.json()["id"]

        # Delete the item
        response = client.delete(f"/items/{item_id}")

        assert response.status_code == 204

        # Verify item is deleted
        get_response = client.get(f"/items/{item_id}")
        assert get_response.status_code == 404

    def test_delete_item_not_found(self):
        """Test deleting a non-existent item."""
        response = client.delete("/items/9999")

        assert response.status_code == 404

    def test_item_response_structure(self):
        """Test that item response has correct structure."""
        response = client.get("/items/1")

        assert response.status_code == 200
        data = response.json()

        # Verify all expected fields
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "price" in data
        assert "quantity" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Verify types
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))
        assert isinstance(data["quantity"], int)
