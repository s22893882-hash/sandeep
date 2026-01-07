"""
Database connection and MongoDB client management.
"""
import random
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

settings = get_settings()

# MongoDB client
client: AsyncIOMotorClient = None

# Database
database: AsyncIOMotorDatabase = None


async def connect_to_mongo():
    """Connect to MongoDB."""
    global client, database
    client = AsyncIOMotorClient(settings.mongodb_url)
    database = client[settings.mongodb_db_name]
    print(f"Connected to MongoDB: {settings.mongodb_url}")


async def close_mongo_connection():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("Closed MongoDB connection")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    return database


async def get_mongo_database() -> AsyncIOMotorDatabase:
    """Dependency to get database instance."""
    return database


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID for database records."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = random.randint(1000, 9999)
    unique_str = f"{prefix}{timestamp}{random_part}"
    return unique_str[:32] if unique_str else generate_id(prefix)
