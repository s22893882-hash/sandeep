# Patient Management APIs

This document describes the Patient Management API implementation for the Federated Health AI Platform.

## Overview

This implementation provides 12 REST API endpoints for complete patient management including profile management, medical history, allergies, health score calculation, and insurance tracking.

## Implemented Endpoints

### Patient Profile Management (3 endpoints)
1. **POST /api/patients/register** - Register a new patient profile
2. **GET /api/patients/profile** - Get authenticated patient's profile
3. **PUT /api/patients/profile** - Update patient profile information

### Medical History (3 endpoints)
4. **POST /api/patients/medical-history** - Add medical history record
5. **GET /api/patients/medical-history** - Retrieve complete medical history
6. **PUT /api/patients/medical-history/{history_id}** - Update medical history record

### Allergies Management (3 endpoints)
7. **POST /api/patients/allergies** - Add allergy record
8. **GET /api/patients/allergies** - Retrieve all patient allergies
9. **DELETE /api/patients/allergies/{allergy_id}** - Remove allergy record

### Health Score & Insurance (3 endpoints)
10. **GET /api/patients/health-score** - Calculate and retrieve patient health score
11. **POST /api/patients/insurance** - Add/update insurance information
12. **GET /api/patients/insurance** - Retrieve patient insurance information

## Database Schema (MongoDB)

### Patients Collection
```javascript
{
  patient_id: String (unique, indexed),
  user_id: String (unique, indexed),
  date_of_birth: String (ISO 8601 date),
  gender: String,
  blood_type: String,
  height_cm: Float,
  weight_kg: Float,
  emergency_contact_name: String,
  emergency_contact_phone: String,
  full_name: String,
  created_at: DateTime,
  updated_at: DateTime,
  is_active: Boolean (default: true)
}
```

### MedicalHistory Collection
```javascript
{
  history_id: String (unique, indexed),
  patient_id: String (indexed),
  condition_name: String,
  diagnosis_date: String (ISO 8601 date),
  status: String ('active' | 'resolved'),
  treatment_notes: String,
  created_at: DateTime,
  updated_at: DateTime
}
```

### Allergies Collection
```javascript
{
  allergy_id: String (unique, indexed),
  patient_id: String (indexed),
  allergen_name: String,
  severity: String ('mild' | 'moderate' | 'severe'),
  reaction_description: String,
  created_at: DateTime
}
```

### Insurance Collection
```javascript
{
  insurance_id: String (unique, indexed),
  patient_id: String (indexed),
  provider_name: String,
  policy_number: String,
  coverage_type: String ('basic' | 'standard' | 'premium'),
  expiry_date: String (ISO 8601 date),
  created_at: DateTime,
  updated_at: DateTime
}
```

## Health Score Calculation Algorithm

The health score is calculated using the following formula:

```
health_score = (bmi_component * 0.30) + (conditions_component * 0.40) + (medications_component * 0.20) + (appointments_component * 0.10)
```

### Component Calculations

- **BMI Component (30% weight):**
  - Formula: `100 - (|bmi - 22.5| * 2)`
  - Capped at 0-100
  - Optimal BMI: 22.5

- **Conditions Component (40% weight):**
  - Formula: `100 - (active_conditions_count * 15)`
  - Capped at 0-100
  - Based on active medical conditions

- **Medications Component (20% weight):**
  - Formula: `100 - (medication_count * 10)`
  - Capped at 0-100
  - Estimated from treatment notes

- **Appointments Component (10% weight):**
  - Formula: `min(recent_appointments / 4, 1) * 100`
  - Appointments in last 3 months
  - 4+ appointments = full score

## Security & Authorization

### JWT Authentication
- All endpoints require JWT authentication (Bearer token)
- Token contains: `user_id`, `email`, `role`
- Configurable secret key and algorithm

### Role-Based Access Control
- **Patients**: Can access and modify their own data
- **Doctors**: Can view patient data (via appointments/consultations)
- **Admins**: Full access to all patient data

### Testing Mode
- In test environment, authentication is bypassed
- Fake tokens are accepted for test scenarios
- Ensures testability without full auth setup

## Code Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── auth.py                    # Authentication & authorization utilities
│   ├── database.py                # MongoDB connection & utilities
│   ├── models/                   # Pydantic data models
│   │   ├── __init__.py
│   │   ├── common.py
│   │   └── patient.py
│   ├── routers/                  # FastAPI route handlers
│   │   ├── __init__.py
│   │   └── patients.py
│   └── services/                 # Business logic layer
│       ├── __init__.py
│       ├── patient_service.py
│       └── health_score_service.py
├── main.py                         # FastAPI application entry point
├── requirements.txt
└── tests/
    ├── test_patients.py              # Unit tests for services
    ├── test_patients_integration.py  # Integration tests
    ├── test_auth_module.py          # Auth module tests
    └── test_database_module.py      # Database module tests
```

## Testing

### Test Coverage
- **65 tests** total
- **Unit tests**: Service and business logic tests
- **Integration tests**: Full endpoint testing
- **Coverage**: ~64% (target: 80%)

### Running Tests
```bash
cd backend
source venv/bin/activate
pytest tests/ -v --cov=app --cov-report=html
```

## Error Handling

All endpoints properly handle:
- Duplicate registrations
- Non-existent resources (404)
- Invalid authentication (401)
- Unauthorized access (403)
- Validation errors (422)
- Server errors (500)

## Dependencies

- `fastapi` - Web framework
- `motor` - Async MongoDB driver
- `pymongo` - MongoDB driver
- `python-jose[cryptography]` - JWT handling
- `pydantic` - Data validation

## Configuration

Required environment variables:
```bash
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=federated_health
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=test|production
```

## Integration Points

### User Management APIs
- Patient registration requires valid `user_id` from User Management
- Profile can be linked to user account

### Doctor Management APIs
- Doctors can view patient profiles via appointment links
- Access control via patient-doctor relationships

### Appointment System
- Health score calculation queries appointment history
- Recent appointments affect health score

## Future Enhancements

1. **Email Notifications**: Insurance expiry reminders
2. **Medication Management**: Dedicated medications table
3. **Appointment Integration**: Real appointment data for health score
4. **Audit Logging**: Complete access logging for compliance
5. **FHIR Integration**: Healthcare data standards compliance
6. **File Upload**: Medical document attachments
7. **Bulk Operations**: Batch patient data updates

## API Documentation

Swagger UI available at: `http://localhost:8000/docs`

All endpoints are fully documented with:
- Request schemas
- Response schemas
- Authentication requirements
- Error responses
- Example requests/responses
