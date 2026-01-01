import os
import pytest
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch
import asyncio

os.environ["ENVIRONMENT"] = "test"


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


@pytest.fixture
def test_user():
    """Create a test user fixture."""
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "is_active": True,
        "is_verified": True,
        "created_at": "2024-01-01T00:00:00Z",
    }


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
    with patch("jwt.decode") as mock:
        mock.return_value = {
            "sub": "1",
            "email": "test@example.com",
            "exp": 9999999999,
        }
        yield mock


@pytest.fixture
def mock_stripe():
    """Mock Stripe API."""
    with patch("stripe.Customer") as mock_customer, \
         patch("stripe.PaymentIntent") as mock_payment, \
         patch("stripe.Subscription") as mock_subscription:
        
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
