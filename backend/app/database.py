"""MongoDB database connection and utilities."""
import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from datetime import datetime


class Database:
    """Database connection manager."""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None

    async def connect(self):
        """Connect to MongoDB."""
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        db_name = os.getenv("MONGODB_DB_NAME", "federated_health")
        self.client = AsyncIOMotorClient(mongodb_url)
        self.database = self.client[db_name]

    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()

    def get_db(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if not self.database:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.database


db = Database()


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID for database records."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import random  # noqa: F401

    random_part = random.randint(1000, 9999)
    unique_str = f"{prefix}{timestamp}{random_part}"
    return unique_str[:32] if unique_str else generate_id(prefix)


async def ensure_indexes(database: AsyncIOMotorDatabase):
    """Create database indexes for collections."""
    # Patients indexes
    await database.patients.create_index([("user_id", 1)], unique=True)
    await database.patients.create_index([("patient_id", 1)], unique=True)
    await database.patients.create_index([("email", 1)])

    # Medical history indexes
    await database.medical_history.create_index([("patient_id", 1)])
    await database.medical_history.create_index([("history_id", 1)], unique=True)

    # Allergies indexes
    await database.allergies.create_index([("patient_id", 1)])
    await database.allergies.create_index([("allergy_id", 1)], unique=True)

    # Insurance indexes
    await database.insurance.create_index([("patient_id", 1)])
    await database.insurance.create_index([("insurance_id", 1)], unique=True)
