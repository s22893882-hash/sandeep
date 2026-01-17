# Appointment Booking System API Documentation

## Overview
This document describes the appointment booking system APIs implemented for Phase 3, Task 1.

## Features
- ✅ Appointment booking with conflict detection
- ✅ Double-booking prevention
- ✅ Time validation (past date rejection)
- ✅ Authorization checks (patient privacy)
- ✅ Appointment listing with pagination
- ✅ Appointment rescheduling
- ✅ Appointment cancellation
- ✅ Appointment history tracking

## API Endpoints

### 1. POST /api/appointments/book
Book a new appointment with conflict detection.

**Request Body:**
```json
{
  "patient_id": "PT123456",
  "doctor_id": "DOC123456",
  "appointment_date": "2024-02-01",
  "appointment_time": "10:00",
  "reason": "Annual checkup",
  "notes": "First visit"
}
```

**Response (201 Created):**
```json
{
  "appointment_id": "APT123456",
  "status": "pending",
  "confirmation_details": {
    "appointment_date": "2024-02-01",
    "appointment_time": "10:00",
    "doctor_id": "DOC123456"
  }
}
```

**Rate Limit:** 5 requests per 15 minutes

**Validation:**
- Appointment date must be in the future
- Time slot must be available (no conflicts)
- Doctor must be available at the requested time

---

### 2. GET /api/appointments
List patient appointments with optional filtering and pagination.

**Query Parameters:**
- `status` (optional): Filter by status (pending/confirmed/completed/cancelled)
- `limit` (optional): Number of results per page (default: 10, max: 100)
- `offset` (optional): Number of results to skip (default: 0)

**Response (200 OK):**
```json
{
  "appointments": [
    {
      "appointment_id": "APT123456",
      "patient_id": "PT123456",
      "doctor_id": "DOC123456",
      "appointment_date": "2024-02-01",
      "appointment_time": "10:00",
      "duration_minutes": 30,
      "reason": "Annual checkup",
      "notes": "First visit",
      "status": "pending",
      "cancellation_reason": null,
      "created_at": "2024-01-17T10:00:00Z",
      "updated_at": "2024-01-17T10:00:00Z",
      "cancelled_at": null
    }
  ],
  "total": 15,
  "limit": 10,
  "offset": 0
}
```

**Authorization:** Patient can only see their own appointments

---

### 3. GET /api/appointments/{id}
Get detailed information about a specific appointment.

**Response (200 OK):**
```json
{
  "appointment_id": "APT123456",
  "patient_id": "PT123456",
  "doctor_id": "DOC123456",
  "appointment_date": "2024-02-01",
  "appointment_time": "10:00",
  "duration_minutes": 30,
  "reason": "Annual checkup",
  "notes": "First visit",
  "status": "pending",
  "cancellation_reason": null,
  "created_at": "2024-01-17T10:00:00Z",
  "updated_at": "2024-01-17T10:00:00Z",
  "cancelled_at": null
}
```

**Authorization:**
- Patients can view their own appointments
- Doctors can view appointments assigned to them
- Admins can view all appointments

---

### 4. PUT /api/appointments/{id}
Update appointment details.

**Request Body:**
```json
{
  "notes": "Updated notes",
  "appointment_date": "2024-02-02",
  "appointment_time": "14:00"
}
```

**Response (200 OK):**
Returns updated appointment object.

**Validation:**
- Cannot update completed or cancelled appointments
- New time slot must be available if rescheduling
- New date must be in the future

---

### 5. DELETE /api/appointments/{id}
Cancel an appointment.

**Request Body:**
```json
{
  "cancellation_reason": "Patient unavailable"
}
```

**Response (200 OK):**
```json
{
  "appointment_id": "APT123456",
  "status": "cancelled",
  "cancelled_at": "2024-01-17T12:00:00Z",
  "message": "Appointment cancelled successfully"
}
```

**Validation:**
- Can only cancel pending or confirmed appointments
- Cannot cancel completed appointments

---

### 6. GET /api/appointments/{patient_id}/history
Get appointment history for a patient.

**Query Parameters:**
- `limit` (optional): Number of results per page (default: 10, max: 100)
- `offset` (optional): Number of results to skip (default: 0)

**Response (200 OK):**
```json
{
  "appointments": [...],
  "total": 25,
  "limit": 10,
  "offset": 0
}
```

**Authorization:** Patients can only view their own history; admins can view any patient's history

---

### 7. PUT /api/appointments/{id}/reschedule
Reschedule an appointment to a new date and time.

**Request Body:**
```json
{
  "new_appointment_date": "2024-02-03",
  "new_appointment_time": "15:00"
}
```

**Response (200 OK):**
Returns updated appointment object.

**Validation:**
- Can only reschedule pending or confirmed appointments
- New time slot must be available
- New date must be in the future

---

## Data Models

### Appointment
- `appointment_id`: Unique identifier (string)
- `patient_id`: Patient identifier (string)
- `doctor_id`: Doctor identifier (string)
- `appointment_date`: Date in ISO 8601 format (string)
- `appointment_time`: Time in HH:MM format (string)
- `duration_minutes`: Appointment duration (integer, default: 30)
- `reason`: Reason for appointment (string)
- `notes`: Optional notes (string)
- `status`: Appointment status (pending/confirmed/completed/cancelled)
- `cancellation_reason`: Optional cancellation reason (string)
- `created_at`: Creation timestamp (datetime)
- `updated_at`: Last update timestamp (datetime)
- `cancelled_at`: Cancellation timestamp (datetime, optional)

### Doctor Availability
- `availability_id`: Unique identifier (string)
- `doctor_id`: Doctor identifier (string)
- `day_of_week`: Day of week (0-6, 0=Monday)
- `start_time`: Start time in HH:MM format (string)
- `end_time`: End time in HH:MM format (string)
- `slot_duration_minutes`: Duration of each slot (integer, default: 30)
- `is_available`: Availability status (boolean)
- `created_at`: Creation timestamp (datetime)
- `updated_at`: Last update timestamp (datetime)

---

## Business Logic

### Conflict Detection
The system prevents double-booking by checking:
1. Existing appointments on the same date
2. Time slot overlaps (considering duration)
3. Doctor availability schedule

### Time Validation
- All appointments must be scheduled in the future
- Past dates are rejected with appropriate error messages
- Time format validation (HH:MM)

### Authorization
- Patients can only access their own appointments
- Doctors can access appointments assigned to them
- Admins have full access to all appointments

### Rate Limiting
- Appointment booking is rate-limited to 5 requests per 15 minutes
- Prevents abuse and spam bookings

---

## Database Collections

### appointments
Stores all appointment records with indexes on:
- `patient_id` (for fast patient queries)
- `doctor_id` (for fast doctor queries)
- `appointment_date` (for date-based queries)

### doctor_availability
Stores doctor availability schedules with indexes on:
- `doctor_id`
- `day_of_week`

---

## Testing

### Unit Tests (20 tests)
- ✅ Successful appointment booking
- ✅ Double-booking prevention
- ✅ Past date rejection
- ✅ Invalid time slot handling
- ✅ Appointment retrieval with authorization
- ✅ Appointment updates and rescheduling
- ✅ Appointment cancellation
- ✅ Pagination functionality
- ✅ Status filtering
- ✅ Time validation

**Test Coverage:** 79% for appointment-related code

### Running Tests
```bash
cd backend
pytest tests/test_appointments.py -v
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Appointment must be scheduled in the future"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied"
}
```

### 404 Not Found
```json
{
  "detail": "Appointment not found or access denied"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "appointment_date"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Future Enhancements
- Email notifications for appointment confirmations
- SMS reminders for upcoming appointments
- Doctor-side appointment management
- Recurring appointments
- Waiting list functionality
- Integration with calendar systems
