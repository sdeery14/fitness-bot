# Client Timezone Detection Implementation

## Summary

Implemented automatic timezone detection and transmission from the client browser to ensure all AI agents receive datetime context in the user's actual timezone.

## Problem

Previously, the backend was using the user's stored timezone (defaulting to "UTC"), but there was no way for the client to communicate its actual browser timezone to the backend. This meant:
- New users always got "UTC" until manually changed
- Users couldn't automatically update timezone when traveling
- AI trace showed "UTC" even when user was in a different timezone

## Solution

### Frontend Changes

1. **Created `frontend/src/lib/timezone.ts`**:
   - `getBrowserTimezone()` - Detects browser timezone using `Intl.DateTimeFormat().resolvedOptions().timeZone`
   - `isValidTimezone()` - Validates IANA timezone strings
   - `formatDateInTimezone()` - Formats dates in user's timezone

2. **Updated `frontend/src/lib/auth.ts`**:
   - Added timezone to login request body
   - User timezone updated automatically on each login

3. **Updated `frontend/src/components/auth/signup-form.tsx`**:
   - Added timezone to registration request body
   - New users get correct timezone from the start

### Backend Changes

1. **Updated `backend/src/api/v1/auth.py`**:
   - Added `timezone` field to `RegisterRequest` schema (optional, defaults to "UTC")
   - Added `timezone` field to `LoginRequest` schema (optional)
   - Pass timezone to auth service methods

2. **Updated `backend/src/services/auth_service.py`**:
   - Added `timezone` parameter to `register()` method
   - Added `timezone` parameter to `login()` method
   - Login automatically updates user timezone if provided (handles traveling users)

3. **Updated `backend/src/api/v1/users.py`**:
   - Added `timezone` field to `UpdateUserRequest` schema
   - Pass timezone to user service update method

4. **Updated `backend/src/services/user_service.py`**:
   - Added `timezone` parameter to `update_user()` method
   - Allows manual timezone updates via PATCH /users/me

5. **Updated `backend/src/api/v1/ai_agent.py`**:
   - Added `timezone` field to `SendMessageRequest` schema (optional)
   - Pass `timezone_override` to ai_service for per-message overrides

6. **Updated `backend/src/services/ai_service.py`**:
   - Added `timezone_override` parameter to `continue_conversation()` method
   - Uses override if provided, otherwise uses user's stored timezone
   - Ensures all datetime context uses the correct timezone

### Documentation

1. **Updated `specs/001-ai-fitness-planner/quickstart.md`**:
   - Added "Timezone Detection & Handling" section
   - Documented automatic detection flow
   - Provided examples for timezone updates and per-message overrides
   - Listed all implementation files

2. **Created `backend/test_timezone_detection.py`**:
   - Test script demonstrating timezone detection
   - Shows datetime formatting across timezones
   - Documents complete API flow

## Usage

### Automatic (Recommended)

1. **New Users**: Timezone detected and saved during registration
2. **Returning Users**: Timezone updated on each login (handles traveling)
3. **All Messages**: AI agents receive datetime in user's timezone

### Manual Updates

```bash
# Update timezone via API
curl -X PATCH http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{"timezone": "Europe/Paris"}'
```

### Per-Message Override

```bash
# Override timezone for a specific message
curl -X POST http://localhost:8000/api/v1/ai/conversations/$id/messages \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What should I eat for breakfast?",
    "timezone": "America/Los_Angeles"
  }'
```

## Testing

1. **Register a new user** via frontend signup form
2. **Check database**: `SELECT email, timezone FROM users;`
3. **Send a message** and verify AI trace shows correct timezone
4. **Change timezone** via PATCH endpoint and verify next message uses new timezone

## Example AI Context

**Before** (always UTC):
```
Current Date and Time: Sunday, December 07, 2025 at 06:28 PM (UTC)
User Message: i want to learn cross country skiing this winter
```

**After** (user's actual timezone):
```
Current Date and Time: Saturday, December 07, 2025 at 01:28 PM (America/New_York)
User Message: i want to learn cross country skiing this winter
```

## Files Modified

- `frontend/src/lib/timezone.ts` (new)
- `frontend/src/lib/auth.ts`
- `frontend/src/components/auth/signup-form.tsx`
- `backend/src/api/v1/auth.py`
- `backend/src/api/v1/users.py`
- `backend/src/api/v1/ai_agent.py`
- `backend/src/services/auth_service.py`
- `backend/src/services/user_service.py`
- `backend/src/services/ai_service.py`
- `specs/001-ai-fitness-planner/quickstart.md`
- `backend/test_timezone_detection.py` (new)

## Benefits

1. **Accurate Time Context**: AI agents always know user's actual local time
2. **Better Recommendations**: Time-appropriate meal and workout suggestions
3. **Automatic Updates**: Timezone synced on every login (no manual work)
4. **Travel Support**: Per-message overrides for users in different timezones
5. **International Support**: Works with all IANA timezones worldwide
