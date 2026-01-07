import os
import pytest
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from httpx import AsyncClient, ASGITransport
from mongomock import MongoClient
from datetime import datetime

os.environ["ENVIRONMENT"] = "test"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB_NAME"] = "test_federated_health_ai"


class MockAsyncDatabase:
    """Mock async database using mongomock."""

    def __init__(self, db_name):
        self.client = MongoClient()
        self.db = self.client[db_name]

    def __getitem__(self, name):
        collection = self.db[name]
        return MockAsyncCollection(collection)

    def __getattr__(self, name):
        return self[name]

    async def drop_database(self, name):
        self.client.drop_database(name)

    def close(self):
        self.client.close()


class MockAsyncCursor:
    """Mock async cursor for motor compatibility."""

    def __init__(self, cursor):
        self.cursor = cursor

    def sort(self, *args, **kwargs):
        self.cursor.sort(*args, **kwargs)
        return self

    def limit(self, *args, **kwargs):
        self.cursor.limit(*args, **kwargs)
        return self

    async def to_list(self, length=None):
        return list(self.cursor)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.cursor)
        except StopIteration:
            raise StopAsyncIteration


class MockAsyncCollection:
    """Mock async collection using mongomock."""

    def __init__(self, collection):
        self.collection = collection

    async def find_one(self, query=None):
        if query:
            return self.collection.find_one(query)
        return None

    def find(self, query=None, projection=None, sort=None, limit=None):
        cursor = self.collection.find(query or {}, projection)
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        return MockAsyncCursor(cursor)

    async def insert_one(self, document):
        # Remove None values from document before insert
        clean_doc = {k: v for k, v in document.items() if v is not None}
        result = self.collection.insert_one(clean_doc)
        return Mock(inserted_id=str(result.inserted_id))

    async def update_one(self, query, update):
        return self.collection.update_one(query, update)

    async def find_one_and_update(self, query, update, return_document=None):
        from pymongo import ReturnDocument

        if return_document == ReturnDocument.AFTER:
            doc = self.collection.find_one(query)
            if doc:
                self.collection.update_one(query, update)
                return self.collection.find_one(query)
        return self.collection.find_one_and_update(query, update)

    async def delete_one(self, query):
        return self.collection.delete_one(query)

    async def delete_many(self, query):
        return self.collection.delete_many(query)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db():
    """Mock database connection."""
    db = Mock()
    db.execute = AsyncMock()
    db.fetch_all = AsyncMock(return_value=[])
    db.fetch_one = AsyncMock(return_value=None)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest.fixture(scope="session")
async def global_db():
    """Create MongoDB test database for the session."""
    db = MockAsyncDatabase(os.environ["MONGODB_DB_NAME"])

    yield db

    # Cleanup
    await db.drop_database(os.environ["MONGODB_DB_NAME"])
    db.close()


@pytest.fixture
async def db(global_db):
    """Get database for this test."""
    # Clean up collections before each test
    await global_db.users.delete_many({})
    await global_db.otps.delete_many({})
    await global_db.password_resets.delete_many({})
    yield global_db


@pytest.fixture
async def test_user(db):
    """Create a test user in database."""
    from app.utils.password import hash_password

    user_data = {
        "email": "test@example.com",
        "password_hash": hash_password("TestPassword123!"),
        "full_name": "Test User",
        "phone_number": "+1234567890",
        "date_of_birth": datetime(1990, 1, 1),
        "address": None,
        "profile_photo_url": None,
        "user_type": "patient",
        "verification_status": "pending",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": None,
        "deleted_at": None,
    }

    result = await db.users.insert_one(user_data)
    user_id = result.inserted_id

    # Generate and store OTP
    from app.utils.otp import generate_otp, get_otp_expiry

    otp_code = generate_otp()
    await db.otps.insert_one(
        {
            "email": user_data["email"],
            "otp_code": otp_code,
            "expires_at": get_otp_expiry(),
            "created_at": datetime.utcnow(),
            "used": False,
        }
    )

    # Return user dict with ID as string
    user_data["user_id"] = str(user_id)
    return user_data


@pytest.fixture
async def verified_user(db):
    """Create a verified test user in database."""
    from app.utils.password import hash_password

    user_data = {
        "email": "verified@example.com",
        "password_hash": hash_password("TestPassword123!"),
        "full_name": "Verified User",
        "phone_number": "+1234567890",
        "date_of_birth": datetime(1990, 1, 1),
        "address": None,
        "profile_photo_url": None,
        "user_type": "patient",
        "verification_status": "verified",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": None,
        "deleted_at": None,
    }

    result = await db.users.insert_one(user_data)
    user_id = result.inserted_id

    # Return user dict with ID as string
    user_data["user_id"] = str(user_id)
    return user_data


@pytest.fixture
async def client(db):
    """Create test HTTP client."""
    # Import app here to avoid circular imports
    from app.main import app

    # Initialize database
    from app.database import get_database

    # Override the database dependency
    async def override_get_database():
        return db

    app.dependency_overrides[get_database] = override_get_database

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(verified_user, db):
    """Create authorization headers for authenticated requests."""
    from app.utils.jwt import create_access_token

    token_data = {
        "sub": verified_user["user_id"],
        "email": verified_user["email"],
        "user_type": verified_user["user_type"],
    }
    access_token = create_access_token(token_data)

    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_admin_user():
    """Create a test admin user fixture."""
    return {
        "id": 2,
        "email": "admin@example.com",
        "username": "adminuser",
        "is_active": True,
        "is_verified": True,
        "is_admin": True,
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def auth_token():
    """Generate a mock JWT token."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"


@pytest.fixture
def mock_jwt_decode():
    """Mock JWT decode function."""
    with patch("jose.jwt.decode") as mock:
        mock.return_value = {
            "sub": "1",
            "email": "test@example.com",
            "exp": 9999999999,
        }
        yield mock


@pytest.fixture
def mock_stripe():
    """Mock Stripe API."""
    with patch("stripe.Customer") as mock_customer, patch("stripe.PaymentIntent") as mock_payment, patch(
        "stripe.Subscription"
    ) as mock_subscription:
        mock_customer.create = Mock(return_value={"id": "cus_test123"})
        mock_customer.retrieve = Mock(return_value={"id": "cus_test123", "email": "test@example.com"})

        mock_payment.create = Mock(return_value={"id": "pi_test123", "status": "succeeded"})
        mock_payment.retrieve = Mock(return_value={"id": "pi_test123", "status": "succeeded"})

        mock_subscription.create = Mock(return_value={"id": "sub_test123", "status": "active"})

        yield {
            "customer": mock_customer,
            "payment": mock_payment,
            "subscription": mock_subscription,
        }


@pytest.fixture
def mock_email_service():
    """Mock email service."""
    with patch("smtplib.SMTP") as mock:
        smtp_instance = Mock()
        smtp_instance.sendmail = Mock()
        smtp_instance.quit = Mock()
        mock.return_value.__enter__ = Mock(return_value=smtp_instance)
        mock.return_value.__exit__ = Mock()
        yield smtp_instance


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    redis = Mock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.exists = AsyncMock(return_value=False)
    redis.expire = AsyncMock()
    return redis


@pytest.fixture
def mock_s3_client():
    """Mock AWS S3 client."""
    with patch("boto3.client") as mock:
        s3 = Mock()
        s3.upload_fileobj = Mock()
        s3.download_fileobj = Mock()
        s3.delete_object = Mock()
        s3.generate_presigned_url = Mock(return_value="https://s3.amazonaws.com/bucket/key")
        mock.return_value = s3
        yield s3


@pytest.fixture
async def test_client():
    """Create a test HTTP client."""
    from unittest.mock import MagicMock

    client = MagicMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    client.patch = AsyncMock()
    return client


@pytest.fixture
def sample_request_data():
    """Sample request data for testing."""
    return {
        "name": "Test Item",
        "description": "Test description",
        "price": 99.99,
        "quantity": 10,
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)
    # Ensure test environment variables are restored
    os.environ["ENVIRONMENT"] = "test"
    os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
    os.environ["MONGODB_DB_NAME"] = "test_federated_health_ai"


@pytest.fixture
def mock_paypal():
    """Mock PayPal API."""
    with patch("paypalrestsdk.Payment") as mock:
        payment = Mock()
        payment.create = Mock(return_value=True)
        payment.id = "PAYID-TEST123"
        payment.state = "approved"
        mock.return_value = payment
        yield payment
