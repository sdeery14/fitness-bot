# API Documentation - AI-Powered Fitness Planner

**Version**: 1.0  
**Base URL**: `http://localhost:8000/api/v1` (development)  
**Last Updated**: November 17, 2025

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Patterns](#common-patterns)
4. [Endpoints](#endpoints)
   - [Auth Endpoints](#auth-endpoints)
   - [User Endpoints](#user-endpoints)
   - [Fitness Plan Endpoints](#fitness-plan-endpoints)
   - [Schedule Endpoints](#schedule-endpoints)
   - [Progress Endpoints](#progress-endpoints)
   - [AI/Conversation Endpoints](#aiconversation-endpoints)
5. [Error Codes](#error-codes)
6. [Rate Limiting](#rate-limiting)
7. [Testing](#testing)

---

## Overview

The AI-Powered Fitness Planner API is a REST API that provides endpoints for:
- User authentication and profile management
- AI-powered fitness plan generation via conversational interface
- Daily schedule management with workout and meal tracking
- Progress tracking with body measurements and photos
- Schedule adaptation based on disruptions

All endpoints return JSON responses and use standard HTTP status codes. Authentication is required for all endpoints except auth endpoints.

---

## Authentication

### JWT Token-Based Authentication

The API uses JWT (JSON Web Token) for authentication. After logging in, you'll receive an `access_token` that must be included in subsequent requests.

**Include the token in the Authorization header:**

```http
Authorization: Bearer <your_access_token>
```

**Token Expiration:**
- Access tokens expire after 24 hours
- Refresh tokens can be used to obtain new access tokens without re-logging in

**Obtaining Tokens:**
1. Register a new account with `POST /api/v1/auth/register`
2. Login with `POST /api/v1/auth/login` to receive tokens
3. Use `POST /api/v1/auth/refresh` to refresh expired access tokens

---

## Common Patterns

### Success Response Format

All successful responses follow this structure:

```json
{
  "status": "success",
  "data": {
    /* Response payload */
  },
  "metadata": {
    "timestamp": "2025-11-17T10:30:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Error Response Format

All error responses follow this structure:

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": {
      /* Optional additional context */
    }
  },
  "metadata": {
    "timestamp": "2025-11-17T10:30:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Paginated Response Format

Endpoints that return lists support pagination:

```json
{
  "status": "success",
  "data": {
    "items": [/* Array of items */],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 100,
      "total_pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

**Pagination Query Parameters:**
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)

---

## Endpoints

### Auth Endpoints

#### POST /api/v1/auth/register

Create a new user account.

**Authentication**: None required

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "date_of_birth": "1990-01-15",
  "current_fitness_level": "beginner"
}
```

**Request Validation**:
- `email`: Valid email format, max 255 characters
- `password`: Min 8 characters, at least 1 uppercase, 1 lowercase, 1 digit
- `full_name`: Min 2 characters, max 100 characters
- `date_of_birth`: ISO 8601 date format, user must be 13+ years old
- `current_fitness_level`: One of `beginner`, `intermediate`, `advanced`

**Response** (201 Created):
```json
{
  "status": "success",
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "full_name": "John Doe",
      "current_fitness_level": "beginner",
      "created_at": "2025-11-17T10:30:00Z"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

**Errors**:
- `400 BAD_REQUEST`: Invalid email format, weak password, invalid fitness level
- `409 CONFLICT`: Email already registered
- `422 UNPROCESSABLE_ENTITY`: Validation errors

---

#### POST /api/v1/auth/login

Authenticate user and receive JWT tokens.

**Authentication**: None required

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "full_name": "John Doe"
    }
  }
}
```

**Errors**:
- `401 UNAUTHORIZED`: Invalid credentials
- `404 NOT_FOUND`: User not found

---

#### POST /api/v1/auth/refresh

Refresh an expired access token using a refresh token.

**Authentication**: None required (uses refresh token)

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

**Errors**:
- `401 UNAUTHORIZED`: Invalid or expired refresh token

---

### User Endpoints

#### GET /api/v1/users/me

Get current authenticated user's profile.

**Authentication**: Required

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "current_fitness_level": "intermediate",
    "date_of_birth": "1990-01-15",
    "dietary_restrictions": ["gluten-free", "dairy-free"],
    "equipment_access": ["home", "dumbbells", "resistance_bands"],
    "preferred_workout_days": ["monday", "wednesday", "friday"],
    "timezone": "America/New_York",
    "created_at": "2025-11-17T10:30:00Z",
    "updated_at": "2025-11-17T11:00:00Z"
  }
}
```

**Errors**:
- `401 UNAUTHORIZED`: Missing or invalid token

---

#### PATCH /api/v1/users/me

Update current user's profile.

**Authentication**: Required

**Request Body** (all fields optional):
```json
{
  "full_name": "John Doe Jr.",
  "current_fitness_level": "advanced",
  "dietary_restrictions": ["vegetarian"],
  "equipment_access": ["gym", "full_equipment"],
  "preferred_workout_days": ["tuesday", "thursday", "saturday"],
  "timezone": "America/Los_Angeles"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe Jr.",
    "current_fitness_level": "advanced",
    "dietary_restrictions": ["vegetarian"],
    "equipment_access": ["gym", "full_equipment"],
    "updated_at": "2025-11-17T12:00:00Z"
  }
}
```

**Errors**:
- `400 BAD_REQUEST`: Invalid field values
- `401 UNAUTHORIZED`: Missing or invalid token

---

### Fitness Plan Endpoints

#### POST /api/v1/fitness-plans

Create a new fitness plan. This endpoint is typically called by the AI agent after a conversation concludes with plan generation.

**Authentication**: Required

**Request Body**:
```json
{
  "goal_description": "Lose 15 pounds in 3 months",
  "goal_type": "weight_loss",
  "duration_weeks": 12,
  "start_date": "2025-11-18",
  "plan_snapshot": {
    "version": "1.0",
    "phases": [
      {
        "phase_number": 1,
        "name": "Foundation Phase",
        "duration_weeks": 4,
        "focus": "Building base fitness and establishing habits"
      }
    ],
    "workout_frequency": "4 days per week",
    "nutrition_approach": "500 calorie deficit"
  }
}
```

**Response** (201 Created):
```json
{
  "status": "success",
  "data": {
    "id": "plan-uuid",
    "user_id": "user-uuid",
    "goal_description": "Lose 15 pounds in 3 months",
    "goal_type": "weight_loss",
    "duration_weeks": 12,
    "start_date": "2025-11-18",
    "target_end_date": "2026-02-09",
    "current_status": "active",
    "current_phase_number": 1,
    "created_at": "2025-11-17T10:30:00Z"
  }
}
```

**Errors**:
- `400 BAD_REQUEST`: Invalid plan data, invalid dates
- `401 UNAUTHORIZED`: Missing or invalid token
- `409 CONFLICT`: User already has an active plan

---

#### GET /api/v1/fitness-plans/{plan_id}

Get detailed information about a specific fitness plan.

**Authentication**: Required

**Path Parameters**:
- `plan_id` - UUID of the fitness plan

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "plan-uuid",
    "user_id": "user-uuid",
    "goal_description": "Lose 15 pounds in 3 months",
    "goal_type": "weight_loss",
    "duration_weeks": 12,
    "start_date": "2025-11-18",
    "target_end_date": "2026-02-09",
    "current_status": "active",
    "current_phase_number": 1,
    "plan_snapshot": {
      "version": "1.0",
      "phases": [/* full phase details */],
      "workout_frequency": "4 days per week",
      "nutrition_approach": "500 calorie deficit"
    },
    "workout_plan": {
      "id": "workout-plan-uuid",
      "workout_frequency_per_week": 4,
      "progression_strategy": "Progressive overload with 5% increases every 2 weeks",
      "workouts": [/* array of workout details */]
    },
    "meal_plan": {
      "id": "meal-plan-uuid",
      "daily_calorie_target": 1800,
      "macros": {
        "protein_grams": 140,
        "carbs_grams": 180,
        "fat_grams": 50
      },
      "meals": [/* array of meal details */]
    },
    "created_at": "2025-11-17T10:30:00Z",
    "updated_at": "2025-11-17T11:00:00Z"
  }
}
```

**Errors**:
- `401 UNAUTHORIZED`: Missing or invalid token
- `403 FORBIDDEN`: Plan belongs to different user
- `404 NOT_FOUND`: Plan not found

---

#### GET /api/v1/fitness-plans/active

Get the current user's active fitness plan.

**Authentication**: Required

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "plan-uuid",
    "goal_description": "Lose 15 pounds in 3 months",
    "goal_type": "weight_loss",
    "current_status": "active",
    "current_phase_number": 1,
    "start_date": "2025-11-18",
    "days_into_plan": 5,
    "completion_percentage": 4.2
  }
}
```

**Errors**:
- `401 UNAUTHORIZED`: Missing or invalid token
- `404 NOT_FOUND`: No active plan found

---

#### PATCH /api/v1/fitness-plans/{plan_id}

Update a fitness plan (e.g., pause, resume, complete).

**Authentication**: Required

**Path Parameters**:
- `plan_id` - UUID of the fitness plan

**Request Body**:
```json
{
  "current_status": "paused"
}
```

**Valid Status Transitions**:
- `active` → `paused`, `completed`, `abandoned`
- `paused` → `active`, `abandoned`

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "plan-uuid",
    "current_status": "paused",
    "updated_at": "2025-11-17T12:00:00Z"
  }
}
```

**Errors**:
- `400 BAD_REQUEST`: Invalid status transition
- `401 UNAUTHORIZED`: Missing or invalid token
- `403 FORBIDDEN`: Plan belongs to different user
- `404 NOT_FOUND`: Plan not found

---

### Schedule Endpoints

#### GET /api/v1/schedules/today

Get today's schedule with all workouts and meals for the current date.

**Authentication**: Required

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "date": "2025-11-17",
    "day_of_week": "sunday",
    "entries": [
      {
        "id": "entry-uuid-1",
        "entry_type": "workout",
        "entry_date": "2025-11-17",
        "entry_time": "08:00:00",
        "completion_status": "completed",
        "completed_at": "2025-11-17T08:45:00Z",
        "user_notes": "Felt great! Increased weight on squats.",
        "workout": {
          "id": "workout-uuid",
          "name": "Lower Body Strength",
          "type": "strength",
          "duration_minutes": 45,
          "intensity": "moderate",
          "description": "Focus on compound leg movements"
        }
      },
      {
        "id": "entry-uuid-2",
        "entry_type": "meal",
        "entry_date": "2025-11-17",
        "entry_time": "12:00:00",
        "completion_status": "scheduled",
        "meal": {
          "id": "meal-uuid",
          "name": "Grilled Chicken Salad",
          "meal_type": "lunch",
          "calories": 450,
          "protein_grams": 40,
          "carbs_grams": 30,
          "fat_grams": 18
        }
      }
    ],
    "summary": {
      "total_workouts": 2,
      "completed_workouts": 1,
      "total_meals": 4,
      "completed_meals": 2,
      "total_calories_planned": 1800,
      "total_calories_logged": 900
    }
  }
}
```

**Errors**:
- `401 UNAUTHORIZED`: Missing or invalid token
- `404 NOT_FOUND`: No active plan or schedule not generated yet

---

#### GET /api/v1/schedules/upcoming

Get upcoming schedule entries for the next N days.

**Authentication**: Required

**Query Parameters**:
- `days` - Number of days to fetch (default: 7, max: 14)

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "start_date": "2025-11-18",
    "end_date": "2025-11-24",
    "entries": [
      {
        "id": "entry-uuid",
        "entry_type": "workout",
        "entry_date": "2025-11-18",
        "entry_time": "08:00:00",
        "completion_status": "scheduled",
        "workout": {
          "name": "Upper Body Push",
          "type": "strength",
          "duration_minutes": 45
        }
      }
      /* ... more entries ... */
    ],
    "grouped_by_date": {
      "2025-11-18": [/* entries for this date */],
      "2025-11-19": [/* entries for this date */]
    }
  }
}
```

**Errors**:
- `400 BAD_REQUEST`: Invalid days parameter
- `401 UNAUTHORIZED`: Missing or invalid token

---

#### POST /api/v1/schedules/entries/{entry_id}/complete

Mark a schedule entry (workout or meal) as completed.

**Authentication**: Required

**Path Parameters**:
- `entry_id` - UUID of the schedule entry

**Request Body** (optional):
```json
{
  "user_notes": "Felt great! Increased weight on squats.",
  "actual_duration_minutes": 50
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "entry-uuid",
    "entry_type": "workout",
    "completion_status": "completed",
    "completed_at": "2025-11-17T08:45:00Z",
    "user_notes": "Felt great! Increased weight on squats."
  }
}
```

**Errors**:
- `400 BAD_REQUEST`: Entry already completed
- `401 UNAUTHORIZED`: Missing or invalid token
- `403 FORBIDDEN`: Entry belongs to different user
- `404 NOT_FOUND`: Entry not found

---

#### POST /api/v1/schedules/entries/{entry_id}/skip

Mark a schedule entry as skipped with a reason.

**Authentication**: Required

**Path Parameters**:
- `entry_id` - UUID of the schedule entry

**Request Body**:
```json
{
  "reason": "Not feeling well, need rest day"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "entry-uuid",
    "completion_status": "skipped",
    "user_notes": "Not feeling well, need rest day",
    "skipped_at": "2025-11-17T09:00:00Z"
  }
}
```

**Errors**:
- `400 BAD_REQUEST`: Missing skip reason, entry already completed/skipped
- `401 UNAUTHORIZED`: Missing or invalid token
- `403 FORBIDDEN`: Entry belongs to different user
- `404 NOT_FOUND`: Entry not found

---

### Progress Endpoints

#### GET /api/v1/progress

Get progress summary and statistics for the current fitness plan.

**Authentication**: Required

**Query Parameters**:
- `fitness_plan_id` - UUID of fitness plan (defaults to active plan)

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "fitness_plan_id": "plan-uuid",
    "days_into_plan": 35,
    "completion_percentage": 29.2,
    "adherence_rate": {
      "overall": 87,
      "workout": 92,
      "nutrition": 82
    },
    "current_streak": {
      "days": 7,
      "type": "workout"
    },
    "longest_streak": {
      "days": 14,
      "type": "workout"
    },
    "completed_workouts": 32,
    "total_workouts_planned": 48,
    "completed_meals": 98,
    "total_meals_planned": 140,
    "body_measurements": {
      "latest_weight": {
        "value": 182.5,
        "unit": "lbs",
        "recorded_at": "2025-11-17T07:00:00Z"
      },
      "starting_weight": {
        "value": 195.0,
        "unit": "lbs",
        "recorded_at": "2025-10-13T07:00:00Z"
      },
      "change": -12.5
    },
    "milestones_reached": [
      {
        "name": "First Week Complete",
        "achieved_at": "2025-10-20T10:00:00Z"
      },
      {
        "name": "Lost 10 Pounds",
        "achieved_at": "2025-11-10T07:00:00Z"
      }
    ]
  }
}
```

**Errors**:
- `401 UNAUTHORIZED`: Missing or invalid token
- `404 NOT_FOUND`: Plan not found

---

#### POST /api/v1/progress/measurements

Record a new body measurement (weight, body fat %, etc).

**Authentication**: Required

**Request Body**:
```json
{
  "fitness_plan_id": "plan-uuid",
  "record_type": "weight",
  "record_date": "2025-11-17",
  "value": 182.5,
  "unit": "lbs",
  "notes": "Weighed first thing in the morning"
}
```

**Valid Record Types**:
- `weight`
- `body_fat_percentage`
- `chest_circumference`
- `waist_circumference`
- `hip_circumference`
- `thigh_circumference`
- `arm_circumference`

**Response** (201 Created):
```json
{
  "status": "success",
  "data": {
    "id": "measurement-uuid",
    "fitness_plan_id": "plan-uuid",
    "record_type": "weight",
    "record_date": "2025-11-17",
    "value": 182.5,
    "unit": "lbs",
    "notes": "Weighed first thing in the morning",
    "created_at": "2025-11-17T07:15:00Z"
  }
}
```

**Errors**:
- `400 BAD_REQUEST`: Invalid record type, invalid value
- `401 UNAUTHORIZED`: Missing or invalid token
- `404 NOT_FOUND`: Plan not found

---

#### GET /api/v1/progress/measurements

Get measurement history with filtering and pagination.

**Authentication**: Required

**Query Parameters**:
- `fitness_plan_id` - UUID of fitness plan (defaults to active plan)
- `record_type` - Filter by measurement type (optional)
- `start_date` - Start of date range (ISO 8601, optional)
- `end_date` - End of date range (ISO 8601, optional)
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": "measurement-uuid",
        "record_type": "weight",
        "record_date": "2025-11-17",
        "value": 182.5,
        "unit": "lbs",
        "notes": "Weighed first thing in the morning",
        "created_at": "2025-11-17T07:15:00Z"
      }
      /* ... more measurements ... */
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 45,
      "total_pages": 3,
      "has_next": true,
      "has_prev": false
    },
    "statistics": {
      "average": 185.2,
      "min": 182.5,
      "max": 195.0,
      "change": -12.5,
      "change_percentage": -6.4
    }
  }
}
```

**Errors**:
- `400 BAD_REQUEST`: Invalid date range or parameters
- `401 UNAUTHORIZED`: Missing or invalid token

---

### AI/Conversation Endpoints

#### POST /api/v1/ai/conversations

Start a new AI conversation for plan generation or modifications.

**Authentication**: Required

**Request Body**:
```json
{
  "conversation_type": "plan_generation",
  "initial_message": "I want to lose 15 pounds in 3 months"
}
```

**Valid Conversation Types**:
- `plan_generation` - Create a new fitness plan
- `plan_modification` - Modify an existing plan
- `general_question` - General fitness questions

**Response** (201 Created):
```json
{
  "status": "success",
  "data": {
    "id": "conversation-uuid",
    "conversation_type": "plan_generation",
    "status": "active",
    "created_at": "2025-11-17T10:00:00Z",
    "messages": [
      {
        "id": "message-uuid",
        "sender_type": "user",
        "content": "I want to lose 15 pounds in 3 months",
        "created_at": "2025-11-17T10:00:00Z"
      }
    ]
  }
}
```

**Errors**:
- `400 BAD_REQUEST`: Invalid conversation type
- `401 UNAUTHORIZED`: Missing or invalid token

---

#### POST /api/v1/ai/conversations/{conversation_id}/messages

Send a message in an existing conversation.

**Authentication**: Required

**Path Parameters**:
- `conversation_id` - UUID of the conversation

**Request Body**:
```json
{
  "content": "I have access to a gym with full equipment"
}
```

**Response** (201 Created):
```json
{
  "status": "success",
  "data": {
    "id": "message-uuid",
    "conversation_id": "conversation-uuid",
    "sender_type": "user",
    "content": "I have access to a gym with full equipment",
    "created_at": "2025-11-17T10:05:00Z",
    "ai_processing": true
  }
}
```

**Note**: After sending a message, connect to the SSE stream endpoint to receive the AI's streaming response.

**Errors**:
- `400 BAD_REQUEST`: Empty message content
- `401 UNAUTHORIZED`: Missing or invalid token
- `403 FORBIDDEN`: Conversation belongs to different user
- `404 NOT_FOUND`: Conversation not found

---

#### GET /api/v1/ai/conversations/{conversation_id}/stream

Server-Sent Events (SSE) stream for real-time AI responses.

**Authentication**: Required

**Path Parameters**:
- `conversation_id` - UUID of the conversation

**Response** (200 OK - SSE Stream):
```
event: message_chunk
data: {"content": "Based on ", "metadata": {"chunk_index": 0}}

event: message_chunk
data: {"content": "your goal ", "metadata": {"chunk_index": 1}}

event: message_chunk
data: {"content": "and equipment access...", "metadata": {"chunk_index": 2}}

event: message_complete
data: {"message_id": "message-uuid", "full_content": "Based on your goal and equipment access..."}

event: plan_generated
data: {"fitness_plan_id": "plan-uuid", "status": "active"}
```

**Event Types**:
- `message_chunk` - Incremental AI response text
- `message_complete` - Full AI message completed
- `plan_generated` - Fitness plan successfully created
- `error` - Error occurred during processing

**Connection Management**:
- Keep-alive heartbeat every 15 seconds
- Auto-reconnect with exponential backoff on disconnect
- Maximum stream duration: 5 minutes

**Errors**:
- `401 UNAUTHORIZED`: Missing or invalid token
- `403 FORBIDDEN`: Conversation belongs to different user
- `404 NOT_FOUND`: Conversation not found

---

#### GET /api/v1/ai/conversations/{conversation_id}

Get conversation history with all messages.

**Authentication**: Required

**Path Parameters**:
- `conversation_id` - UUID of the conversation

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "conversation-uuid",
    "conversation_type": "plan_generation",
    "status": "completed",
    "created_at": "2025-11-17T10:00:00Z",
    "completed_at": "2025-11-17T10:15:00Z",
    "messages": [
      {
        "id": "message-uuid-1",
        "sender_type": "user",
        "content": "I want to lose 15 pounds in 3 months",
        "created_at": "2025-11-17T10:00:00Z"
      },
      {
        "id": "message-uuid-2",
        "sender_type": "ai",
        "content": "That's a great goal! To create the perfect plan...",
        "created_at": "2025-11-17T10:00:05Z"
      }
      /* ... more messages ... */
    ],
    "generated_plan_id": "plan-uuid"
  }
}
```

**Errors**:
- `401 UNAUTHORIZED`: Missing or invalid token
- `403 FORBIDDEN`: Conversation belongs to different user
- `404 NOT_FOUND`: Conversation not found

---

#### POST /api/v1/ai/reschedule

Report a disruption and request AI-generated schedule adaptations.

**Authentication**: Required

**Request Body**:
```json
{
  "fitness_plan_id": "plan-uuid",
  "disruption_type": "illness",
  "severity": "moderate",
  "start_date": "2025-11-17",
  "end_date": "2025-11-19",
  "description": "Caught a cold, need to rest for a few days"
}
```

**Valid Disruption Types**:
- `illness` - Sick or injured
- `travel` - Away from home
- `work` - Work commitments
- `personal` - Personal reasons
- `other` - Other disruptions

**Valid Severity Levels**:
- `minor` - 1-2 days impact
- `moderate` - 3-5 days impact
- `severe` - 6+ days impact

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "disruption_id": "disruption-uuid",
    "adaptation_summary": {
      "workouts_rescheduled": 3,
      "meals_adjusted": 0,
      "new_target_end_date": "2026-02-12",
      "phase_adjustments": [
        {
          "phase_number": 2,
          "original_end_date": "2025-12-15",
          "new_end_date": "2025-12-18"
        }
      ]
    },
    "recommendations": [
      "Focus on light stretching during recovery",
      "Stay hydrated and maintain protein intake",
      "Resume workouts gradually when feeling better"
    ],
    "ai_reasoning": "Based on your moderate illness, I've rescheduled 3 workouts..."
  }
}
```

**Errors**:
- `400 BAD_REQUEST`: Invalid disruption data, end date before start date
- `401 UNAUTHORIZED`: Missing or invalid token
- `404 NOT_FOUND`: Plan not found

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid authentication token |
| `FORBIDDEN` | 403 | User doesn't have permission to access resource |
| `NOT_FOUND` | 404 | Requested resource doesn't exist |
| `CONFLICT` | 409 | Request conflicts with existing data (e.g., email already registered) |
| `VALIDATION_ERROR` | 422 | Request data failed validation |
| `BAD_REQUEST` | 400 | Invalid request format or parameters |
| `INTERNAL_ERROR` | 500 | Server encountered an unexpected error |
| `SERVICE_UNAVAILABLE` | 503 | External service (OpenAI, database) is unavailable |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests, rate limit exceeded |

---

## Rate Limiting

The API implements rate limiting to prevent abuse and ensure fair usage.

### Rate Limit Tiers

| Endpoint Category | Requests per Minute | Window |
|------------------|---------------------|--------|
| Auth endpoints | 5 | 60 seconds |
| General endpoints | 100 | 60 seconds |
| AI streaming | 10 | 60 seconds |

### Rate Limit Headers

All responses include rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1700232600
X-RateLimit-Window: 60
```

**Header Descriptions**:
- `X-RateLimit-Limit` - Maximum requests allowed in window
- `X-RateLimit-Remaining` - Requests remaining in current window
- `X-RateLimit-Reset` - Unix timestamp when the window resets
- `X-RateLimit-Window` - Window duration in seconds

### Rate Limit Exceeded Response

```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please try again in 45 seconds.",
    "details": {
      "retry_after": 45,
      "limit": 100,
      "window": 60
    }
  }
}
```

**Status Code**: 429 Too Many Requests

---

## Testing

### Example cURL Commands

#### Register a New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User",
    "date_of_birth": "1990-01-15",
    "current_fitness_level": "beginner"
  }'
```

#### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

#### Get User Profile

```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Get Today's Schedule

```bash
curl -X GET http://localhost:8000/api/v1/schedules/today \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Mark Workout Complete

```bash
curl -X POST http://localhost:8000/api/v1/schedules/entries/ENTRY_ID/complete \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_notes": "Great workout!",
    "actual_duration_minutes": 50
  }'
```

#### Start AI Conversation

```bash
curl -X POST http://localhost:8000/api/v1/ai/conversations \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_type": "plan_generation",
    "initial_message": "I want to build muscle in 12 weeks"
  }'
```

#### Connect to SSE Stream

```bash
curl -X GET http://localhost:8000/api/v1/ai/conversations/CONVERSATION_ID/stream \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: text/event-stream"
```

### Testing with Postman

1. **Import Collection**: Import the OpenAPI spec from `/api/v1/openapi.json`
2. **Set Environment Variables**:
   - `base_url`: `http://localhost:8000/api/v1`
   - `access_token`: Your JWT token after login
3. **Test Auth Flow**: Register → Login → Get Profile
4. **Test Plan Creation**: Start Conversation → Send Messages → Monitor Stream
5. **Test Schedule**: Get Today → Get Upcoming → Mark Complete

### Running Contract Tests

```bash
# Backend contract tests
cd backend
pytest tests/contract/ -v

# Expected: All API contract tests pass
# Validates: Request/response formats, error codes, status codes
```

---

## Additional Resources

- **OpenAPI Specification**: `/api/v1/openapi.json`
- **Swagger UI**: `/docs` (available in development)
- **ReDoc**: `/redoc` (available in development)
- **Architecture Documentation**: `docs/architecture.md`
- **External Integrations**: `docs/external-integrations.md`
- **Deployment Guide**: `docs/deployment.md`

---

## Support

For API issues or questions:
- Check the error code reference above
- Review response `metadata.request_id` for debugging
- Consult the architecture documentation for system design
- Check server logs with the request ID for detailed error traces

---

**Last Updated**: November 17, 2025  
**API Version**: 1.0  
**Maintained by**: Fitness Bot Development Team
