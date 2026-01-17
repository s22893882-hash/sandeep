"""
Comprehensive test suite for Consultation Features System - Phase 3 Module 2.
Tests all 18 APIs with high coverage and performance validation.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.consultation import (
    ConsultationStatus,
    MessageType,
    PrescriptionStatus,
    DocumentType,
    FeedbackPriority,
)
from app.database import database


class TestConsultationSystem:
    """Comprehensive test suite for consultation system."""

    @pytest.fixture
    def client(self):
        """Test client fixture."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers."""
        return {"Authorization": "Bearer test-token"}

    @pytest.fixture
    def mock_user_patient(self):
        """Mock patient user."""
        return {
            "user_id": "USER_PATIENT_123",
            "user_type": "patient",
            "email": "patient@test.com",
            "full_name": "Test Patient"
        }

    @pytest.fixture
    def mock_user_doctor(self):
        """Mock doctor user."""
        return {
            "user_id": "USER_DOCTOR_456", 
            "user_type": "doctor",
            "email": "doctor@test.com",
            "full_name": "Dr. Test Doctor"
        }

    @pytest.fixture
    def consultation_data(self):
        """Mock consultation start data."""
        return {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456",
            "reason": "General consultation for headache"
        }

    @pytest.fixture
    def message_data(self):
        """Mock message data."""
        return {
            "message_text": "Hello doctor, I have been having headaches for 3 days",
            "message_type": "text"
        }

    @pytest.fixture
    def prescription_data(self):
        """Mock prescription data."""
        return {
            "medications": [
                {
                    "medication_name": "Paracetamol",
                    "dosage": "500mg",
                    "frequency": "Twice daily",
                    "duration": "5 days",
                    "instructions": "Take after meals"
                }
            ],
            "instructions": "Complete the full course even if symptoms improve"
        }

    @pytest.fixture
    def clinical_notes_data(self):
        """Mock clinical notes data."""
        return {
            "notes_text": "Patient presents with tension headaches. Likely stress-related. Advised rest and hydration.",
            "vitals": {
                "blood_pressure": "120/80",
                "heart_rate": 72,
                "temperature": 36.5,
                "weight": 70.0
            },
            "diagnosis": "Tension headache",
            "treatment_plan": "Rest, hydration, and stress management. Follow up in 1 week if symptoms persist."
        }

    @pytest.fixture
    def document_data(self):
        """Mock document data."""
        return {
            "document_type": "lab",
            "description": "Blood test results from last week"
        }

    @pytest.fixture
    def feedback_data(self):
        """Mock feedback data."""
        return {
            "rating": 5,
            "feedback_text": "Excellent consultation, very thorough and helpful doctor",
            "would_recommend": True,
            "anonymous": False
        }

    # Test 1: Core Consultation Management
    @pytest.mark.asyncio
    async def test_start_consultation_success(self, client, auth_headers, consultation_data, mock_user_patient, mock_user_doctor):
        """Test starting a new consultation session."""
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        assert response.status_code == 201
        data = response.json()
        assert "consultation_id" in data
        assert "session_token" in data
        assert "start_time" in data
        assert data["status"] == "initiated"

    @pytest.mark.asyncio
    async def test_get_consultation_details(self, client, auth_headers, mock_user_patient):
        """Test retrieving consultation details."""
        # First create a consultation
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            response = client.get(
                f"/api/consultations/{consultation_id}",
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["consultation_id"] == consultation_id
        assert data["patient_id"] == "USER_PATIENT_123"
        assert data["doctor_id"] == "USER_DOCTOR_456"

    # Test 2: Chat & Messaging
    @pytest.mark.asyncio
    async def test_send_message_success(self, client, auth_headers, mock_user_patient, message_data):
        """Test sending a consultation message."""
        # Create consultation first
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            response = client.post(
                f"/api/consultations/{consultation_id}/message",
                json=message_data,
                headers=auth_headers
            )
        
        assert response.status_code == 201
        data = response.json()
        assert "message_id" in data
        assert "timestamp" in data
        assert data["delivery_status"] == "sent"

    @pytest.mark.asyncio
    async def test_get_messages_success(self, client, auth_headers, mock_user_patient):
        """Test retrieving consultation messages."""
        # Create consultation and send message
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        message_data = {
            "message_text": "Test message",
            "message_type": "text"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            # Start consultation
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            # Send message
            client.post(
                f"/api/consultations/{consultation_id}/message",
                json=message_data,
                headers=auth_headers
            )
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            # Get messages
            response = client.get(
                f"/api/consultations/{consultation_id}/messages",
                headers=auth_headers
            )
        
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) >= 1
        assert messages[0]["message_text"] == "Test message"

    # Test 3: Prescriptions
    @pytest.mark.asyncio
    async def test_create_prescription_success(self, client, auth_headers, mock_user_doctor, prescription_data):
        """Test creating a prescription."""
        # Create consultation first
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            response = client.post(
                f"/api/consultations/{consultation_id}/prescription",
                json=prescription_data,
                headers=auth_headers
            )
        
        assert response.status_code == 201
        data = response.json()
        assert "prescription_id" in data
        assert "qr_code" in data
        assert data["prescription_status"] == "active"

    @pytest.mark.asyncio
    async def test_get_prescriptions_success(self, client, auth_headers, mock_user_doctor, prescription_data):
        """Test retrieving prescriptions."""
        # Create consultation and prescription
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            client.post(
                f"/api/consultations/{consultation_id}/prescription",
                json=prescription_data,
                headers=auth_headers
            )
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            response = client.get(
                f"/api/consultations/{consultation_id}/prescriptions",
                headers=auth_headers
            )
        
        assert response.status_code == 200
        prescriptions = response.json()
        assert len(prescriptions) >= 1
        assert "medications" in prescriptions[0]

    # Test 4: Clinical Notes
    @pytest.mark.asyncio
    async def test_create_clinical_notes_success(self, client, auth_headers, mock_user_doctor, clinical_notes_data):
        """Test creating clinical notes."""
        # Create consultation first
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            response = client.post(
                f"/api/consultations/{consultation_id}/notes",
                json=clinical_notes_data,
                headers=auth_headers
            )
        
        assert response.status_code == 201
        data = response.json()
        assert "notes_id" in data
        assert "notes_summary" in data
        assert "follow_up_required" in data

    @pytest.mark.asyncio
    async def test_get_clinical_notes_success(self, client, auth_headers, mock_user_doctor, clinical_notes_data):
        """Test retrieving clinical notes."""
        # Create consultation and notes
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            client.post(
                f"/api/consultations/{consultation_id}/notes",
                json=clinical_notes_data,
                headers=auth_headers
            )
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            response = client.get(
                f"/api/consultations/{consultation_id}/notes",
                headers=auth_headers
            )
        
        assert response.status_code == 200
        notes = response.json()
        assert len(notes) >= 1
        assert "notes_text" in notes[0]
        assert "diagnosis" in notes[0]

    # Test 5: Document Management
    @pytest.mark.asyncio
    async def test_attach_document_success(self, client, auth_headers, mock_user_patient, document_data):
        """Test attaching a document."""
        # Create consultation first
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        # Mock file upload
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            with patch('builtins.open', create=True):
                response = client.post(
                    f"/api/consultations/{consultation_id}/attach-document",
                    files={"file": ("test.pdf", b"test content", "application/pdf")},
                    data=document_data,
                    headers=auth_headers
                )
        
        assert response.status_code == 201
        data = response.json()
        assert "document_id" in data
        assert "upload_status" in data

    @pytest.mark.asyncio
    async def test_get_documents_success(self, client, auth_headers, mock_user_patient, document_data):
        """Test retrieving documents."""
        # Create consultation and attach document
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            with patch('builtins.open', create=True):
                client.post(
                    f"/api/consultations/{consultation_id}/attach-document",
                    files={"file": ("test.pdf", b"test content", "application/pdf")},
                    data=document_data,
                    headers=auth_headers
                )
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            response = client.get(
                f"/api/consultations/{consultation_id}/documents",
                headers=auth_headers
            )
        
        assert response.status_code == 200
        documents = response.json()
        assert len(documents) >= 1
        assert "document_type" in documents[0]

    # Test 6: Consultation Lifecycle
    @pytest.mark.asyncio
    async def test_close_consultation_success(self, client, auth_headers, mock_user_doctor):
        """Test closing a consultation."""
        # Create consultation first
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        close_data = {
            "end_notes": "Consultation completed successfully",
            "duration": 30
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            response = client.put(
                f"/api/consultations/{consultation_id}/close",
                json=close_data,
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "duration_minutes" in data

    @pytest.mark.asyncio
    async def test_schedule_follow_up_success(self, client, auth_headers, mock_user_doctor):
        """Test scheduling follow-up."""
        # Create consultation first
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        follow_up_data = {
            "follow_up_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "reason": "Follow-up for headache symptoms",
            "priority": "medium"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            response = client.post(
                f"/api/consultations/{consultation_id}/follow-up",
                json=follow_up_data,
                headers=auth_headers
            )
        
        assert response.status_code == 201
        data = response.json()
        assert "follow_up_id" in data
        assert "scheduled_time" in data

    # Test 7: Feedback & Ratings
    @pytest.mark.asyncio
    async def test_create_feedback_success(self, client, auth_headers, mock_user_patient, feedback_data):
        """Test creating feedback."""
        # Create consultation first
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        # Close consultation first (required for feedback)
        close_data = {
            "end_notes": "Completed",
            "duration": 30
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            client.put(
                f"/api/consultations/{consultation_id}/close",
                json=close_data,
                headers=auth_headers
            )
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            response = client.post(
                f"/api/consultations/{consultation_id}/feedback",
                json=feedback_data,
                headers=auth_headers
            )
        
        assert response.status_code == 201
        data = response.json()
        assert "feedback_id" in data
        assert "feedback_summary" in data

    @pytest.mark.asyncio
    async def test_get_feedback_success(self, client, auth_headers, mock_user_patient, feedback_data):
        """Test retrieving feedback."""
        # Create consultation, close it, and add feedback
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        # Close consultation
        close_data = {"end_notes": "Completed", "duration": 30}
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            client.put(
                f"/api/consultations/{consultation_id}/close",
                json=close_data,
                headers=auth_headers
            )
        
        # Create feedback
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            client.post(
                f"/api/consultations/{consultation_id}/feedback",
                json=feedback_data,
                headers=auth_headers
            )
        
        # Get feedback
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            response = client.get(
                f"/api/consultations/{consultation_id}/feedback",
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 5
        assert data["would_recommend"] == True

    # Test 8: Consultation Retrieval
    @pytest.mark.asyncio
    async def test_get_my_consultations_success(self, client, auth_headers, mock_user_patient):
        """Test retrieving patient consultations."""
        # Create consultation
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            response = client.get(
                "/api/consultations/my-consultations?status=all&limit=10&offset=0",
                headers=auth_headers
            )
        
        assert response.status_code == 200
        consultations = response.json()
        assert len(consultations) >= 1

    @pytest.mark.asyncio
    async def test_get_doctor_consultations_success(self, client, auth_headers, mock_user_doctor):
        """Test retrieving doctor consultations."""
        # Create consultation
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        with patch('app.auth.get_current_user', return_value=mock_user_doctor):
            response = client.get(
                "/api/consultations/doctor-consultations?status=all&limit=10&offset=0",
                headers=auth_headers
            )
        
        assert response.status_code == 200
        consultations = response.json()
        assert len(consultations) >= 1

    # Test 9: Video Integration
    @pytest.mark.asyncio
    async def test_generate_video_token_success(self, client, auth_headers, mock_user_patient):
        """Test generating video call token."""
        # Create consultation first
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        token_data = {
            "participant_type": "patient",
            "session_duration": 60
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            response = client.post(
                f"/api/consultations/{consultation_id}/video-token",
                json=token_data,
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "video_token" in data
        assert "channel_name" in data
        assert "rtc_uid" in data

    # Performance Tests
    @pytest.mark.asyncio
    async def test_message_delivery_performance(self, client, auth_headers, mock_user_patient):
        """Test message delivery latency < 200ms."""
        import time
        
        # Create consultation
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        message_data = {
            "message_text": "Performance test message",
            "message_type": "text"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        # Measure message delivery time
        start_time = time.time()
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            response = client.post(
                f"/api/consultations/{consultation_id}/message",
                json=message_data,
                headers=auth_headers
            )
        
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 201
        assert latency < 200, f"Message delivery took {latency}ms, should be < 200ms"

    @pytest.mark.asyncio
    async def test_video_token_generation_performance(self, client, auth_headers, mock_user_patient):
        """Test video token generation < 100ms."""
        import time
        
        # Create consultation
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        token_data = {
            "participant_type": "patient",
            "session_duration": 60
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        # Measure token generation time
        start_time = time.time()
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            response = client.post(
                f"/api/consultations/{consultation_id}/video-token",
                json=token_data,
                headers=auth_headers
            )
        
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 200
        assert latency < 100, f"Video token generation took {latency}ms, should be < 100ms"

    # Security Tests
    @pytest.mark.asyncio
    async def test_unauthorized_access_denied(self, client, auth_headers):
        """Test that unauthorized access is properly denied."""
        # Try to access consultation without proper authorization
        response = client.get(
            "/api/consultations/nonexistent-id",
            headers=auth_headers
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_consultation_authorization(self, client, auth_headers, mock_user_patient):
        """Test that users can only access their own consultations."""
        # Create consultation as patient
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        # Try to access as different user (should be denied)
        other_user = {
            "user_id": "USER_OTHER_789",
            "user_type": "patient",
            "email": "other@test.com"
        }
        
        with patch('app.auth.get_current_user', return_value=other_user):
            response = client.get(
                f"/api/consultations/{consultation_id}",
                headers=auth_headers
            )
        
        assert response.status_code == 404  # Should not find consultation for other user

    # Error Handling Tests
    @pytest.mark.asyncio
    async def test_invalid_consultation_id(self, client, auth_headers, mock_user_patient):
        """Test handling of invalid consultation ID."""
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            response = client.get(
                "/api/consultations/invalid-id",
                headers=auth_headers
            )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_message_data(self, client, auth_headers, mock_user_patient):
        """Test handling of invalid message data."""
        # Create consultation first
        consultation_data = {
            "appointment_id": "APT_12345",
            "patient_id": "USER_PATIENT_123",
            "doctor_id": "USER_DOCTOR_456"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            start_response = client.post(
                "/api/consultations/start",
                json=consultation_data,
                headers=auth_headers
            )
        
        consultation_id = start_response.json()["consultation_id"]
        
        # Send invalid message (empty text)
        invalid_message = {
            "message_text": "",  # Empty text should fail validation
            "message_type": "text"
        }
        
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            response = client.post(
                f"/api/consultations/{consultation_id}/message",
                json=invalid_message,
                headers=auth_headers
            )
        
        assert response.status_code == 422  # Validation error

    # Statistics Test
    @pytest.mark.asyncio
    async def test_consultation_stats(self, client, auth_headers, mock_user_patient):
        """Test consultation statistics endpoint."""
        with patch('app.auth.get_current_user', return_value=mock_user_patient):
            response = client.get(
                "/api/consultations/stats/my-stats",
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_consultations" in data
        assert "status_breakdown" in data
        assert "user_type" in data
        assert data["user_type"] == "patient"


if __name__ == "__main__":
    pytest.main([__file__])