"""
Database connection and MongoDB client management.
"""
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


class DatabaseWrapper:
    """Database wrapper for compatibility with patient services."""

    def get_db(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        return database


# Create db instance for patient services compatibility
db = DatabaseWrapper()
