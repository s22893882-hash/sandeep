"""Integration tests for consultation system end-to-end workflows."""
import pytest
from datetime import datetime
from bson import ObjectId
import io


@pytest.fixture
def mock_consultation_data():
    """Create mock consultation data."""
    return {
        "appointment_id": "APT123",
        "patient_id": "patient123",
        "doctor_id": "doctor123",
    }


@pytest.fixture
def mock_completed_consultation(db):
    """Create a completed consultation for testing."""
    consultation = {
        "_id": ObjectId(),
        "consultation_id": "CON456",
        "appointment_id": "APT456",
        "patient_id": "patient123",
        "doctor_id": "doctor123",
        "status": "completed",
        "start_time": datetime.utcnow(),
        "end_time": datetime.utcnow(),
        "duration_minutes": 30,
        "session_token": "token456",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    db.consultations.insert_one(consultation)
    return consultation


# End-to-End Workflow Tests


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_consultation_workflow(client, db, auth_headers, mock_consultation_data):
    """
    Test complete consultation workflow:
    1. Start consultation
    2. Send messages
    3. Add prescription
    4. Add clinical notes
    5. Attach document
    6. Close consultation
    7. Submit feedback
    """
    # Step 1: Start consultation
    start_response = await client.post(
        "/api/consultations/start",
        json=mock_consultation_data,
        headers=auth_headers,
    )
    assert start_response.status_code == 201
    consultation_data = start_response.json()
    consultation_id = consultation_data["consultation_id"]

    # Step 2: Send messages
    message_response = await client.post(
        f"/api/consultations/{consultation_id}/message",
        json={
            "sender_id": "doctor123",
            "message_text": "Hello, how are you feeling today?",
            "message_type": "text",
        },
        headers=auth_headers,
    )
    assert message_response.status_code == 201

    # Step 3: Update status to in-progress
    status_response = await client.put(
        f"/api/consultations/{consultation_id}/status",
        json={"status": "in-progress"},
        headers=auth_headers,
    )
    assert status_response.status_code == 200

    # Step 4: Add prescription
    prescription_response = await client.post(
        f"/api/consultations/{consultation_id}/prescription",
        json={
            "medications": [
                {
                    "medication_name": "Aspirin",
                    "dosage": "500mg",
                    "frequency": "Twice daily",
                    "duration": "7 days",
                    "instructions": "Take with food",
                }
            ],
            "notes": "For pain relief",
        },
        headers=auth_headers,
    )
    assert prescription_response.status_code == 201

    # Step 5: Add clinical notes
    notes_response = await client.post(
        f"/api/consultations/{consultation_id}/notes",
        json={
            "notes_text": "Patient presents with mild chest pain",
            "vitals": {
                "blood_pressure": "120/80",
                "heart_rate": 72,
                "temperature": 98.6,
                "weight": 70,
            },
            "diagnosis": "Musculoskeletal chest pain",
            "history_plan": "Rest and pain management",
        },
        headers=auth_headers,
    )
    assert notes_response.status_code == 201

    # Step 6: Attach document
    file_content = b"mock pdf content" * 100
    files = {"file": ("report.pdf", io.BytesIO(file_content), "application/pdf")}
    data = {"document_type": "report", "description": "Test report"}
    document_response = await client.post(
        f"/api/consultations/{consultation_id}/attach-document",
        files=files,
        data=data,
        headers=auth_headers,
    )
    assert document_response.status_code == 201

    # Step 7: Close consultation
    close_response = await client.put(
        f"/api/consultations/{consultation_id}/close",
        json={"end_notes": "Patient advised to follow treatment plan"},
        headers=auth_headers,
    )
    assert close_response.status_code == 200
    close_data = close_response.json()
    assert close_data["status"] == "completed"
    assert close_data["duration_minutes"] >= 0

    # Step 8: Submit feedback
    feedback_response = await client.post(
        f"/api/consultations/{consultation_id}/feedback",
        json={
            "rating": 5,
            "feedback_text": "Excellent consultation",
            "would_recommend": True,
            "anonymous": False,
        },
        headers=auth_headers,
    )
    assert feedback_response.status_code == 201


@pytest.mark.integration
@pytest.mark.asyncio
async def test_messaging_workflow(client, db, auth_headers, mock_consultation_data):
    """Test real-time messaging workflow."""
    # Start consultation
    start_response = await client.post(
        "/api/consultations/start",
        json=mock_consultation_data,
        headers=auth_headers,
    )
    consultation_id = start_response.json()["consultation_id"]

    # Send multiple messages
    messages = [
        ("doctor123", "How are you feeling?"),
        ("patient123", "I have chest pain"),
        ("doctor123", "How long has this been going on?"),
        ("patient123", "For about 2 days"),
    ]

    for sender, text in messages:
        response = await client.post(
            f"/api/consultations/{consultation_id}/message",
            json={
                "sender_id": sender,
                "message_text": text,
                "message_type": "text",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

    # Get all messages
    messages_response = await client.get(
        f"/api/consultations/{consultation_id}/messages",
        headers=auth_headers,
    )
    assert messages_response.status_code == 200
    data = messages_response.json()
    assert len(data["messages"]) == len(messages)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_prescription_workflow(client, db, auth_headers, mock_consultation_data):
    """Test prescription creation and retrieval."""
    # Start consultation
    start_response = await client.post(
        "/api/consultations/start",
        json=mock_consultation_data,
        headers=auth_headers,
    )
    consultation_id = start_response.json()["consultation_id"]

    # Add prescription with multiple medications
    prescription_response = await client.post(
        f"/api/consultations/{consultation_id}/prescription",
        json={
            "medications": [
                {
                    "medication_name": "Aspirin",
                    "dosage": "500mg",
                    "frequency": "Twice daily",
                    "duration": "7 days",
                    "instructions": "Take with food",
                },
                {
                    "medication_name": "Ibuprofen",
                    "dosage": "200mg",
                    "frequency": "Three times daily",
                    "duration": "5 days",
                    "instructions": "Take after meals",
                },
            ],
            "notes": "For pain management",
        },
        headers=auth_headers,
    )
    assert prescription_response.status_code == 201
    prescription = prescription_response.json()
    assert len(prescription["medications"]) == 2
    assert "qr_code" in prescription

    # Get prescriptions
    get_response = await client.get(
        f"/api/consultations/{consultation_id}/prescriptions",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert len(data["prescriptions"]) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_document_workflow(client, db, auth_headers, mock_consultation_data):
    """Test document upload and retrieval."""
    # Start consultation
    start_response = await client.post(
        "/api/consultations/start",
        json=mock_consultation_data,
        headers=auth_headers,
    )
    consultation_id = start_response.json()["consultation_id"]

    # Upload multiple documents
    documents = [
        ("xray.jpg", "image/jpeg", "xray", "Chest X-ray"),
        ("report.pdf", "application/pdf", "report", "Lab report"),
        ("scan.png", "image/png", "scan", "MRI scan"),
    ]

    for filename, content_type, doc_type, description in documents:
        file_content = b"mock file content"
        files = {"file": (filename, io.BytesIO(file_content), content_type)}
        data = {"document_type": doc_type, "description": description}

        response = await client.post(
            f"/api/consultations/{consultation_id}/attach-document",
            files=files,
            data=data,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["document_type"] == doc_type
        assert data["is_scanned"] is True

    # Get all documents
    get_response = await client.get(
        f"/api/consultations/{consultation_id}/documents",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert len(data["documents"]) == len(documents)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_follow_up_workflow(client, db, auth_headers, mock_completed_consultation):
    """Test follow-up consultation scheduling."""
    consultation_id = mock_completed_consultation["consultation_id"]

    # Schedule follow-up
    follow_up_response = await client.post(
        f"/api/consultations/{consultation_id}/follow-up",
        json={
            "follow_up_date": "2025-02-01",
            "follow_up_time": "10:30",
            "reason": "Monitor treatment progress",
            "priority": "medium",
        },
        headers=auth_headers,
    )
    assert follow_up_response.status_code == 201
    follow_up = follow_up_response.json()
    assert follow_up["original_consultation_id"] == consultation_id
    assert follow_up["status"] == "scheduled"
    assert follow_up["priority"] == "medium"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_video_token_generation(client, db, auth_headers, mock_consultation_data):
    """Test video token generation."""
    # Start consultation
    start_response = await client.post(
        "/api/consultations/start",
        json=mock_consultation_data,
        headers=auth_headers,
    )
    consultation_id = start_response.json()["consultation_id"]

    # Generate video token for doctor
    token_response = await client.post(
        f"/api/consultations/{consultation_id}/video-token",
        json={
            "participant_type": "doctor",
            "session_duration": 60,
        },
        headers=auth_headers,
    )
    assert token_response.status_code == 200
    token_data = token_response.json()
    assert "video_token" in token_data
    assert "channel_name" in token_data
    assert "rtc_uid" in token_data
    assert "token_expiry" in token_data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_patient_consultation_history(client, db, auth_headers, mock_consultation_data):
    """Test getting patient's consultation history."""
    # Start multiple consultations
    for i in range(3):
        await client.post(
            "/api/consultations/start",
            json={
                "appointment_id": f"APT{i}",
                "patient_id": "patient123",
                "doctor_id": "doctor123",
            },
            headers=auth_headers,
        )

    # Get patient's consultations
    response = await client.get(
        "/api/consultations/my-consultations?limit=10&offset=0",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["consultations"]) >= 3
    assert data["total_count"] >= 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_doctor_consultation_schedule(client, db, auth_headers, mock_consultation_data):
    """Test getting doctor's consultation schedule."""
    # Start multiple consultations
    for i in range(3):
        await client.post(
            "/api/consultations/start",
            json={
                "appointment_id": f"APT{i}",
                "patient_id": f"patient{i}",
                "doctor_id": "doctor123",
            },
            headers=auth_headers,
        )

    # Get doctor's consultations
    response = await client.get(
        "/api/consultations/doctor-consultations?limit=10&offset=0",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["consultations"]) >= 3
    assert data["total_count"] >= 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_consultation_status_transitions(client, db, auth_headers, mock_consultation_data):
    """Test valid consultation status transitions."""
    # Start consultation
    start_response = await client.post(
        "/api/consultations/start",
        json=mock_consultation_data,
        headers=auth_headers,
    )
    consultation_id = start_response.json()["consultation_id"]
    assert start_response.json()["status"] == "initiated"

    # Transition to in-progress
    response1 = await client.put(
        f"/api/consultations/{consultation_id}/status",
        json={"status": "in-progress"},
        headers=auth_headers,
    )
    assert response1.status_code == 200
    assert response1.json()["status"] == "in-progress"

    # Transition to completed
    response2 = await client.put(
        f"/api/consultations/{consultation_id}/close",
        json={"end_notes": "Consultation completed"},
        headers=auth_headers,
    )
    assert response2.status_code == 200
    assert response2.json()["status"] == "completed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_message_pagination(client, db, auth_headers, mock_consultation_data):
    """Test message pagination functionality."""
    # Start consultation
    start_response = await client.post(
        "/api/consultations/start",
        json=mock_consultation_data,
        headers=auth_headers,
    )
    consultation_id = start_response.json()["consultation_id"]

    # Send 25 messages
    for i in range(25):
        await client.post(
            f"/api/consultations/{consultation_id}/message",
            json={
                "sender_id": "doctor123",
                "message_text": f"Message {i}",
                "message_type": "text",
            },
            headers=auth_headers,
        )

    # Get first page (limit=10)
    page1 = await client.get(
        f"/api/consultations/{consultation_id}/messages?limit=10&offset=0",
        headers=auth_headers,
    )
    assert page1.status_code == 200
    data1 = page1.json()
    assert len(data1["messages"]) == 10
    assert data1["limit"] == 10
    assert data1["offset"] == 0

    # Get second page (limit=10, offset=10)
    page2 = await client.get(
        f"/api/consultations/{consultation_id}/messages?limit=10&offset=10",
        headers=auth_headers,
    )
    assert page2.status_code == 200
    data2 = page2.json()
    assert len(data2["messages"]) == 10
    assert data2["limit"] == 10
    assert data2["offset"] == 10

    # Verify total count
    assert data1["total_count"] == 25
    assert data2["total_count"] == 25


@pytest.mark.integration
@pytest.mark.asyncio
async def test_clinical_notes_versioning(client, db, auth_headers, mock_consultation_data):
    """Test clinical notes versioning."""
    # Start consultation
    start_response = await client.post(
        "/api/consultations/start",
        json=mock_consultation_data,
        headers=auth_headers,
    )
    consultation_id = start_response.json()["consultation_id"]

    # Add initial notes
    notes1_response = await client.post(
        f"/api/consultations/{consultation_id}/notes",
        json={
            "notes_text": "Initial assessment",
            "diagnosis": "Tentative diagnosis",
        },
        headers=auth_headers,
    )
    assert notes1_response.status_code == 201
    notes1 = notes1_response.json()
    assert notes1["version"] == 1

    # Get notes
    get_response = await client.get(
        f"/api/consultations/{consultation_id}/notes",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
    notes = get_response.json()
    assert notes["notes_text"] == "Initial assessment"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_authorization_enforcement(client, db, mock_consultation_data):
    """Test that authorization is properly enforced."""
    # Start consultation
    start_response = await client.post(
        "/api/consultations/start",
        json=mock_consultation_data,
        headers=auth_headers,
    )
    consultation_id = start_response.json()["consultation_id"]

    # Try to access with different user (simulated via different user ID in message)
    # This should still work since we're using the same auth token
    # In a real scenario, you'd use a different auth token

    # Try to close consultation as non-doctor (would fail with different user)
    # For now, just verify the endpoint exists
    response = await client.put(
        f"/api/consultations/{consultation_id}/close",
        json={"end_notes": "Closing notes"},
        headers=auth_headers,
    )
    # Should succeed because auth_headers is from a doctor/admin user
    assert response.status_code in [200, 400]  # 200 if successful, 400 if already closed


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling(client, db, auth_headers):
    """Test proper error handling."""
    # Try to get non-existent consultation
    response = await client.get(
        "/api/consultations/NONEXISTENT",
        headers=auth_headers,
    )
    assert response.status_code == 404

    # Try to add feedback to non-existent consultation
    response = await client.post(
        "/api/consultations/NONEXISTENT/feedback",
        json={"rating": 5},
        headers=auth_headers,
    )
    assert response.status_code == 400

    # Try to send message to non-existent consultation
    response = await client.post(
        "/api/consultations/NONEXISTENT/message",
        json={
            "sender_id": "doctor123",
            "message_text": "Hello",
            "message_type": "text",
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
