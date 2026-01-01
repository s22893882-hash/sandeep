"""Items API routes."""
from typing import List

from fastapi import APIRouter, HTTPException, Query, status

from app.logging import get_logger
from app.models import ItemCreate, ItemResponse, ItemUpdate, PaginatedResponse

router = APIRouter(prefix="/items", tags=["Items"])
logger = get_logger(__name__)

# In-memory storage (replace with database in production)
items_db: dict[int, dict] = {
    1: {
        "id": 1,
        "name": "Sample Item",
        "description": "A sample item for demonstration",
        "price": 9.99,
        "quantity": 100,
    },
    2: {
        "id": 2,
        "name": "Premium Item",
        "description": "A premium item with extra features",
        "price": 29.99,
        "quantity": 50,
    },
}
item_id_counter = 3


@router.get("", response_model=List[ItemResponse])
async def list_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
) -> List[ItemResponse]:
    """
    List all items with pagination.

    - **skip**: Number of items to skip (default: 0)
    - **limit**: Maximum number of items to return (default: 10, max: 100)
    """
    logger.info("Listing items", extra={"skip": skip, "limit": limit})

    items = list(items_db.values())[skip : skip + limit]
    return [ItemResponse(**item) for item in items]


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int) -> ItemResponse:
    """
    Get a specific item by ID.

    - **item_id**: The unique identifier of the item
    """
    logger.info("Getting item", extra={"item_id": item_id})

    if item_id not in items_db:
        logger.warning("Item not found", extra={"item_id": item_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )

    return ItemResponse(**items_db[item_id])


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate) -> ItemResponse:
    """
    Create a new item.

    - **name**: Item name (required)
    - **description**: Item description (optional)
    - **price**: Item price, must be greater than 0 (required)
    - **quantity**: Initial quantity (optional, default: 0)
    """
    global item_id_counter

    logger.info("Creating item", extra={"item_name": item.name})

    new_item = {
        "id": item_id_counter,
        **item.model_dump(),
    }
    items_db[item_id_counter] = new_item
    item_id_counter += 1

    logger.info("Item created successfully", extra={"item_id": new_item["id"]})
    return ItemResponse(**new_item)


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item: ItemUpdate) -> ItemResponse:
    """
    Update an existing item.

    - **item_id**: The unique identifier of the item
    - **name**: New name (optional)
    - **description**: New description (optional)
    - **price**: New price (optional)
    - **quantity**: New quantity (optional)
    """
    logger.info("Updating item", extra={"item_id": item_id})

    if item_id not in items_db:
        logger.warning("Item not found", extra={"item_id": item_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )

    # Update only provided fields
    update_data = item.model_dump(exclude_unset=True)
    items_db[item_id].update(update_data)

    logger.info("Item updated successfully", extra={"item_id": item_id})
    return ItemResponse(**items_db[item_id])


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int) -> None:
    """
    Delete an item.

    - **item_id**: The unique identifier of the item
    """
    logger.info("Deleting item", extra={"item_id": item_id})

    if item_id not in items_db:
        logger.warning("Item not found", extra={"item_id": item_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )

    del items_db[item_id]
    logger.info("Item deleted successfully", extra={"item_id": item_id})
