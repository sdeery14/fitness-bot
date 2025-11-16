# API Contracts: AI-Powered Fitness Planner

**Feature**: 001-ai-fitness-planner  
**Date**: 2025-11-15  
**API Version**: v1  
**Base URL**: `/api/v1`

## Overview

This document defines the REST API contracts for the AI-powered fitness planning application. All endpoints follow RESTful principles, return JSON responses, and require authentication (except auth endpoints).

---

## Authentication

All protected endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

JWT tokens are issued by the auth endpoints and validated by the FastAPI middleware.

---

## Common Response Formats

### Success Response
```json
{
  "status": "success",
  "data": { /* response data */ },
  "metadata": {
    "timestamp": "2025-11-15T10:30:00Z",
    "request_id": "uuid"
  }
}
```

### Error Response
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { /* optional additional context */ }
  },
  "metadata": {
    "timestamp": "2025-11-15T10:30:00Z",
    "request_id": "uuid"
  }
}
```

### Paginated Response
```json
{
  "status": "success",
  "data": {
    "items": [ /* array of items */ ],
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

---

## Endpoints

### Auth Endpoints

#### POST /api/v1/auth/register
Create a new user account.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "date_of_birth": "1990-01-15",
  "current_fitness_level": "beginner"
}
```

**Response** (201 Created):
```json
{
  "status": "success",
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "John Doe",
      "created_at": "2025-11-15T10:30:00Z"
    },
    "access_token": "jwt_token",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

**Errors**:
- `400 BAD_REQUEST`: Invalid email format, weak password
- `409 CONFLICT`: Email already registered

---

#### POST /api/v1/auth/login
Authenticate and receive JWT token.

**Request**:
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
    "access_token": "jwt_token",
    "refresh_token": "refresh_jwt_token",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": "uuid",
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
Refresh expired access token.

**Request**:
```json
{
  "refresh_token": "refresh_jwt_token"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "access_token": "new_jwt_token",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

---

### User Endpoints

#### GET /api/v1/users/me
Get current user profile.

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "current_fitness_level": "beginner",
    "date_of_birth": "1990-01-15",
    "dietary_restrictions": ["gluten-free"],
    "equipment_access": ["home", "dumbbells"],
    "preferred_workout_days": ["monday", "wednesday", "friday"],
    "timezone": "America/New_York",
    "created_at": "2025-11-15T10:30:00Z"
  }
}
```

---

#### PATCH /api/v1/users/me
Update user profile.

**Request**:
```json
{
  "full_name": "John Doe Jr.",
  "current_fitness_level": "intermediate",
  "dietary_restrictions": ["vegetarian"],
  "equipment_access": ["gym"]
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe Jr.",
    "current_fitness_level": "intermediate",
    "updated_at": "2025-11-15T11:00:00Z"
  }
}
```

---

### Fitness Plan Endpoints

#### POST /api/v1/fitness-plans
Create a new fitness plan (initiated by AI conversation).

**Request**:
```json
{
  "goal_description": "Lose 15 pounds in 3 months",
  "goal_type": "weight_loss",
  "duration_weeks": 12,
  "start_date": "2025-11-18",
  "plan_snapshot": {
    "version": "1.0",
    "phases": [/* ... */],
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
    "id": "uuid",
    "user_id": "uuid",
    "goal_description": "Lose 15 pounds in 3 months",
    "goal_type": "weight_loss",
    "duration_weeks": 12,
    "start_date": "2025-11-18",
    "target_end_date": "2026-02-09",
    "current_status": "active",
    "created_at": "2025-11-15T10:30:00Z"
  }
}
```

**Errors**:
- `400 BAD_REQUEST`: Invalid plan data
- `409 CONFLICT`: User already has an active plan

---

#### GET /api/v1/fitness-plans/{plan_id}
Get fitness plan details.

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "goal_description": "Lose 15 pounds in 3 months",
    "goal_type": "weight_loss",
    "duration_weeks": 12,
    "start_date": "2025-11-18",
    "target_end_date": "2026-02-09",
    "current_status": "active",
    "current_phase_number": 1,
    "plan_snapshot": {/* full plan structure */},
    "workout_plan": {
      "id": "uuid",
      "workout_frequency_per_week": 4,
      "progression_strategy": "Progressive overload"
    },
    "meal_plan": {
      "id": "uuid",
      "daily_calorie_target": 1800,
      "macronutrient_distribution": {
        "protein_pct": 30,
        "carb_pct": 40,
        "fat_pct": 30
      }
    },
    "phases": [
      {
        "phase_number": 1,
        "name": "Foundation Building",
        "objectives": ["Build habit", "Establish baseline"],
        "duration_weeks": 4,
        "status": "in_progress"
      }
    ]
  }
}
```

**Errors**:
- `404 NOT_FOUND`: Plan not found
- `403 FORBIDDEN`: Plan belongs to another user

---

#### GET /api/v1/fitness-plans/active
Get user's current active plan.

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "goal_description": "Lose 15 pounds in 3 months",
    /* ... same as GET /fitness-plans/{plan_id} */
  }
}
```

**Errors**:
- `404 NOT_FOUND`: No active plan

---

#### PATCH /api/v1/fitness-plans/{plan_id}
Update fitness plan (typically after AI conversation).

**Request**:
```json
{
  "current_status": "paused",
  "plan_snapshot": {/* updated plan structure */}
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "current_status": "paused",
    "updated_at": "2025-11-15T11:00:00Z"
  }
}
```

---

### Schedule Endpoints

#### GET /api/v1/schedules/today
Get today's scheduled workouts and meals.

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "date": "2025-11-15",
    "entries": [
      {
        "id": "uuid",
        "entry_type": "workout",
        "entry_time": null,
        "completion_status": "scheduled",
        "workout": {
          "id": "uuid",
          "name": "Upper Body Strength",
          "workout_type": "strength",
          "estimated_duration_minutes": 45,
          "exercises": [
            {
              "name": "Bench Press",
              "sets": 3,
              "reps": "8-12"
            }
          ]
        }
      },
      {
        "id": "uuid",
        "entry_type": "meal",
        "entry_time": "08:00:00",
        "completion_status": "completed",
        "completed_at": "2025-11-15T08:15:00Z",
        "meal": {
          "id": "uuid",
          "name": "High Protein Breakfast",
          "meal_type": "breakfast",
          "calories": 450
        }
      }
    ],
    "summary": {
      "total_workouts": 1,
      "total_meals": 3,
      "completed_workouts": 0,
      "completed_meals": 1
    }
  }
}
```

---

#### GET /api/v1/schedules/upcoming
Get upcoming schedule (next 14 days).

**Query Parameters**:
- `days`: Number of days to fetch (default: 14, max: 30)

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "entries_by_date": {
      "2025-11-15": [/* entries */],
      "2025-11-16": [/* entries */],
      /* ... */
    },
    "summary": {
      "total_workouts": 8,
      "total_meals": 42,
      "date_range": {
        "start": "2025-11-15",
        "end": "2025-11-28"
      }
    }
  }
}
```

---

#### POST /api/v1/schedules/entries/{entry_id}/complete
Mark a schedule entry as complete.

**Request**:
```json
{
  "user_notes": "Great workout, felt strong!",
  "completed_at": "2025-11-15T10:45:00Z"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "completion_status": "completed",
    "completed_at": "2025-11-15T10:45:00Z",
    "user_notes": "Great workout, felt strong!"
  }
}
```

---

#### POST /api/v1/schedules/entries/{entry_id}/skip
Mark a schedule entry as skipped.

**Request**:
```json
{
  "skipped_reason": "Not feeling well today"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "completion_status": "skipped",
    "skipped_reason": "Not feeling well today"
  }
}
```

---

### Progress Endpoints

#### GET /api/v1/progress
Get progress summary and statistics.

**Query Parameters**:
- `period`: Time period (week, month, all) - default: week

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "period": "week",
    "date_range": {
      "start": "2025-11-08",
      "end": "2025-11-15"
    },
    "adherence": {
      "workout_completion_rate": 87.5,
      "meal_completion_rate": 92.3,
      "overall_adherence_rate": 89.9
    },
    "workouts": {
      "total_scheduled": 8,
      "completed": 7,
      "skipped": 1
    },
    "meals": {
      "total_scheduled": 26,
      "completed": 24,
      "skipped": 2
    },
    "streaks": {
      "current_streak_days": 5,
      "longest_streak_days": 12
    },
    "milestones": [
      {
        "achieved_at": "2025-11-10",
        "description": "Completed first week!",
        "type": "duration"
      }
    ]
  }
}
```

---

#### POST /api/v1/progress/measurements
Log body measurements.

**Request**:
```json
{
  "weight_lbs": 185.5,
  "body_fat_percentage": 22.5,
  "measurements": {
    "chest": 40,
    "waist": 34,
    "arms": 14
  },
  "energy_level": 8,
  "mood": "good",
  "user_notes": "Feeling stronger this week"
}
```

**Response** (201 Created):
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "record_date": "2025-11-15",
    "weight_lbs": 185.5,
    "body_fat_percentage": 22.5,
    "measurements": {
      "chest": 40,
      "waist": 34,
      "arms": 14
    },
    "created_at": "2025-11-15T10:30:00Z"
  }
}
```

---

#### GET /api/v1/progress/measurements
Get measurement history.

**Query Parameters**:
- `start_date`: Filter start date (ISO 8601)
- `end_date`: Filter end date (ISO 8601)

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "measurements": [
      {
        "record_date": "2025-11-15",
        "weight_lbs": 185.5,
        "body_fat_percentage": 22.5,
        "measurements": {"chest": 40, "waist": 34, "arms": 14}
      },
      {
        "record_date": "2025-11-08",
        "weight_lbs": 187.2,
        "body_fat_percentage": 23.1,
        "measurements": {"chest": 40, "waist": 35, "arms": 14}
      }
    ],
    "trends": {
      "weight_change_lbs": -1.7,
      "body_fat_change_pct": -0.6,
      "period_days": 7
    }
  }
}
```

---

### AI Agent Endpoints

#### POST /api/v1/ai/conversations
Start a new conversation with the AI agent.

**Request**:
```json
{
  "conversation_type": "plan_creation",
  "initial_message": "I want to lose 15 pounds in 3 months"
}
```

**Response** (201 Created):
```json
{
  "status": "success",
  "data": {
    "conversation_id": "uuid",
    "conversation_type": "plan_creation",
    "status": "active",
    "started_at": "2025-11-15T10:30:00Z"
  }
}
```

---

#### POST /api/v1/ai/conversations/{conversation_id}/messages
Send a message in an existing conversation.

**Request**:
```json
{
  "message": "I have access to a gym with all equipment"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "message_id": "uuid",
    "conversation_id": "uuid",
    "user_message": {
      "content": "I have access to a gym with all equipment",
      "sent_at": "2025-11-15T10:32:00Z"
    },
    "assistant_response": {
      "content": "Great! Having access to a gym gives us many options...",
      "sent_at": "2025-11-15T10:32:05Z",
      "function_calls": [
        {
          "function": "update_user_preferences",
          "arguments": {"equipment_access": ["gym"]}
        }
      ]
    }
  }
}
```

---

#### GET /api/v1/ai/conversations/{conversation_id}/stream
Stream AI responses (Server-Sent Events).

**Response** (text/event-stream):
```
data: {"type": "start", "conversation_id": "uuid"}

data: {"type": "chunk", "content": "Based on your goal"}

data: {"type": "chunk", "content": " of losing 15 pounds"}

data: {"type": "function_call", "function": "create_plan", "status": "started"}

data: {"type": "function_call", "function": "create_plan", "status": "completed", "result": {"plan_id": "uuid"}}

data: {"type": "chunk", "content": " I've created a personalized plan for you!"}

data: {"type": "complete"}
```

---

#### GET /api/v1/ai/conversations/{conversation_id}
Get conversation history.

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "conversation_type": "plan_creation",
    "status": "active",
    "messages": [
      {
        "sender_type": "user",
        "message_content": "I want to lose 15 pounds",
        "sent_at": "2025-11-15T10:30:00Z"
      },
      {
        "sender_type": "assistant",
        "message_content": "I can help you with that! Let me ask a few questions...",
        "sent_at": "2025-11-15T10:30:02Z"
      }
    ],
    "conversation_context": {
      "intent": "create_plan",
      "collected_info": {"goal": "lose 15 pounds"}
    }
  }
}
```

---

#### POST /api/v1/ai/reschedule
Request AI-powered rescheduling due to disruption.

**Request**:
```json
{
  "disruption_type": "illness",
  "start_date": "2025-11-15",
  "duration_days": 3,
  "description": "I have the flu and need to rest"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "disruption_event_id": "uuid",
    "workouts_rescheduled": 2,
    "meals_affected": 0,
    "timeline_extension_days": 3,
    "new_target_end_date": "2026-02-12",
    "resolution_strategy": "Moved 2 workouts to Week 5, added 3 days to overall plan duration",
    "ai_recommendation": "Focus on rest and recovery. When you're feeling better, we'll ease back in with lighter workouts."
  }
}
```

---

### Workout Endpoints

#### GET /api/v1/workouts/{workout_id}
Get workout details.

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "name": "Upper Body Strength",
    "workout_type": "strength",
    "target_muscle_groups": ["chest", "shoulders", "triceps"],
    "estimated_duration_minutes": 45,
    "intensity_level": "moderate",
    "description": "Full upper body workout focusing on push movements",
    "exercises": [
      {
        "id": "uuid",
        "exercise_order": 1,
        "name": "Bench Press",
        "exercise_type": "compound",
        "target_muscle_groups": ["chest", "triceps", "shoulders"],
        "equipment_required": ["barbell", "bench"],
        "sets": 3,
        "reps": "8-12",
        "rest_seconds": 90,
        "instructions": "Lie on bench, lower bar to chest, press up explosively",
        "form_cues": ["Keep feet planted", "Retract shoulder blades", "Control the descent"]
      }
    ]
  }
}
```

---

#### GET /api/v1/workouts/{workout_id}/alternatives
Get alternative exercises for a workout.

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "workout_id": "uuid",
    "alternatives": [
      {
        "exercise_id": "uuid",
        "original_exercise": "Bench Press",
        "alternatives": [
          {
            "id": "uuid",
            "name": "Dumbbell Press",
            "reason": "Same muscle groups, less technical",
            "difficulty": "easier"
          },
          {
            "id": "uuid",
            "name": "Push-ups",
            "reason": "Bodyweight alternative",
            "difficulty": "easier"
          }
        ]
      }
    ]
  }
}
```

---

### Meal Endpoints

#### GET /api/v1/meals/{meal_id}
Get meal details.

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "name": "High Protein Breakfast",
    "meal_type": "breakfast",
    "calories": 450,
    "protein_grams": 35,
    "carbs_grams": 40,
    "fat_grams": 15,
    "meal_details": {
      "recipe": "Scrambled eggs with whole wheat toast and fruit",
      "ingredients": [
        {"item": "Eggs", "amount": "3 large", "calories": 210},
        {"item": "Whole wheat bread", "amount": "2 slices", "calories": 160},
        {"item": "Berries", "amount": "1 cup", "calories": 80}
      ],
      "instructions": [
        "Scramble eggs in non-stick pan",
        "Toast bread",
        "Serve with fresh berries"
      ]
    },
    "prep_time_minutes": 5,
    "cook_time_minutes": 10,
    "difficulty": "easy"
  }
}
```

---

## Rate Limiting

All endpoints are rate-limited to prevent abuse:

- Auth endpoints: 5 requests per minute per IP
- AI streaming endpoints: 10 concurrent connections per user
- General endpoints: 100 requests per minute per user

Rate limit headers included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1700058000
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Authenticated but not authorized |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate) |
| `VALIDATION_ERROR` | 422 | Request body validation failed |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## Versioning

API versioning via URL path (`/api/v1`, `/api/v2`).

Breaking changes require a new major version. Non-breaking changes (adding optional fields, new endpoints) can be added to existing version.

---

## WebSocket / SSE Endpoints

### SSE: /api/v1/ai/conversations/{conversation_id}/stream

Real-time streaming of AI responses using Server-Sent Events.

**Event Types**:
- `start`: Conversation started
- `chunk`: Text chunk from AI
- `function_call`: AI tool execution
- `complete`: Response complete
- `error`: Error occurred

---

## Summary

This API provides 25+ endpoints organized into 7 categories:
1. **Auth** (3 endpoints): Register, login, refresh
2. **Users** (2 endpoints): Profile management
3. **Fitness Plans** (4 endpoints): CRUD operations
4. **Schedules** (4 endpoints): Daily and upcoming schedules
5. **Progress** (3 endpoints): Tracking and measurements
6. **AI Agent** (5 endpoints): Conversations and streaming
7. **Workouts/Meals** (4 endpoints): Detail views and alternatives

All endpoints follow REST principles, use JWT authentication, implement pagination, and provide comprehensive error handling.
