"""
Database connection and operations for MongoDB.
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings


class Database:
    """MongoDB database client."""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls):
        """Connect to MongoDB."""
        try:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
            cls.db = cls.client[settings.MONGODB_DATABASE]

            # Create indexes
            await cls.create_indexes()
            print("Connected to MongoDB successfully")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    async def create_indexes(cls):
        """Create database indexes for better performance."""
        # Doctors collection indexes
        doctors_collection = cls.db.doctors
        await doctors_collection.create_index("user_id", unique=True)
        await doctors_collection.create_index("license_number", unique=True)
        await doctors_collection.create_index("specialization")
        await doctors_collection.create_index("is_verified")
        await doctors_collection.create_index("average_rating")

        # Users collection indexes
        users_collection = cls.db.users
        await users_collection.create_index("email", unique=True)

        # Appointments collection indexes
        appointments_collection = cls.db.appointments
        await appointments_collection.create_index([("doctor_id", 1), ("date", 1), ("start_time", 1)])
        await appointments_collection.create_index([("patient_id", 1), ("date", 1)])

        # Reviews collection indexes
        reviews_collection = cls.db.reviews
        await reviews_collection.create_index([("doctor_id", 1), ("rating", -1)])

    @classmethod
    async def close(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            print("MongoDB connection closed")


async def init_db():
    """Initialize database connection."""
    await Database.connect()


async def close_db():
    """Close database connection."""
    await Database.close()


async def get_db() -> AsyncIOMotorDatabase:
    """Get database instance."""
    if not Database.db:
        raise Exception("Database not initialized")
    return Database.db
