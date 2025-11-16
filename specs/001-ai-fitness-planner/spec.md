# Feature Specification: AI-Powered Fitness Planner

**Feature Branch**: `001-ai-fitness-planner`  
**Created**: 2025-11-13  
**Status**: Draft  
**Input**: User description: "Build an application that helps users create, follow, and update a fitness plan through a conversation with an AI fitness agent. A fitness plan is made up of a meal plan and a workout plan that helps the users reach their fitness goal. fitness plans can be for any goal over any time period. They can be short and simple to get ready for an upcoming event, or they can be long multi-year pursuits with multiple phases. A schedule can then be maintained for the user that follows the workout and meal plan. The inspiration to build this app is how time consuming fitness training scheduling can be, especially when you are not sure of unexpected obstructions or what days off you will need during training. In addition to helping maintain the users plan and schedule, the AI should also help in ideating new ways to improve things"

## Clarifications

### Session 2025-11-15

- Q: How should meal plans be generated (AI text suggestions only, third-party recipe API, curated database, or AI-generated full recipes)? → A: Use USDA FoodData Central API for nutrition data; AI generates meal suggestions by combining USDA ingredients with calculated portions to hit macro targets
- Q: How should exercises be sourced (AI-generated from scratch, third-party API, curated database, or hybrid approach)? → A: Build a curated database of 200-500 common exercises with standardized attributes (muscle groups, equipment, difficulty, alternatives)
- Q: What authentication method should be used (email/password only, email/password with JWT, OAuth social logins, passwordless magic links, or hybrid)? → A: Email/password with JWT tokens (stateless, scalable)
- Q: How should the system handle users returning after extended absence (2+ weeks) - resume from last date, mark missed items as skipped, prompt for reassessment via AI, or archive old plan? → A: Prompt user to reassess their current state via AI conversation before resuming
- Q: How should AI plan generation handle the 30-second response time target and manage context? → A: Use orchestrated multi-agent architecture with parallel specialist workers (Conversation Agent → Fitness Plan Agent → Workout Plan Agent + Meal Plan Agent running simultaneously); store state/data in Redis/PostgreSQL with storage references instead of passing full data to LLMs; generate plans asynchronously with streaming progress updates and background notifications so users can navigate away

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Initial Fitness Plan via AI Conversation (Priority: P1)

A user new to the application starts a conversation with the AI fitness agent to create their first fitness plan. They describe their fitness goal (e.g., "lose 15 pounds in 3 months", "run a 5K in 8 weeks", "build muscle over 6 months"), current fitness level, dietary preferences, and available time for workouts. The AI guides them through a conversational flow to understand their needs and generates a personalized fitness plan that includes both a workout plan and a meal plan.

**Why this priority**: This is the core value proposition and entry point for all users. Without the ability to create a plan, no other features matter. This delivers immediate value by replacing hours of manual research and planning.

**Independent Test**: Can be fully tested by having a test user start a new conversation, describe a fitness goal, and receive a complete fitness plan with workout and meal components. Success means the user has a actionable plan they can start following immediately.

**Acceptance Scenarios**:

1. **Given** a new user starts the application, **When** they initiate a conversation with the AI and describe their fitness goal, current fitness level, and constraints, **Then** the AI asks clarifying questions about preferences, schedule, dietary restrictions, and equipment access
2. **Given** the AI has gathered sufficient information, **When** the user confirms they're ready to generate the plan, **Then** the system creates a fitness plan containing both workout routines and meal suggestions tailored to their goal
3. **Given** a fitness plan has been created, **When** the user reviews the plan, **Then** they can see the plan structure, duration, phases (if multi-phase), workout schedule, and meal plan overview
4. **Given** a user describes an ambiguous goal like "get healthier", **When** the AI processes this, **Then** the AI asks specific follow-up questions to clarify measurable outcomes (weight loss, strength gain, endurance improvement, etc.)

---

### User Story 2 - Follow and Track Schedule (Priority: P2)

A user with an existing fitness plan wants to follow their workout and meal schedule day-by-day. The application maintains their current position in the plan, shows what workouts and meals are scheduled for today and upcoming days, and allows them to mark items as complete. The user can see their progress over time and track adherence to the plan.

**Why this priority**: Once users have a plan, they need a way to actually follow it. This addresses the core problem of maintaining consistency and tracking progress, which is essential for achieving fitness goals. Without this, users would need to manually track everything in spreadsheets or notes.

**Independent Test**: Can be tested by creating a user with an existing fitness plan, viewing today's scheduled workouts and meals, marking items complete, and verifying that the schedule advances correctly and shows accurate progress tracking.

**Acceptance Scenarios**:

1. **Given** a user has an active fitness plan, **When** they open the application, **Then** they see today's scheduled workouts and meals with clear instructions and timing
2. **Given** a user completes a scheduled workout, **When** they mark it as complete, **Then** the system records the completion, updates progress tracking, and shows the next scheduled workout
3. **Given** a user wants to see their upcoming schedule, **When** they navigate to the schedule view, **Then** they can see workouts and meals planned for the next 7-14 days
4. **Given** a user has been following the plan for several weeks, **When** they view progress, **Then** they can see completion rates, streaks, and adherence statistics
5. **Given** today's date advances, **When** the user opens the app, **Then** the schedule automatically updates to show the current day's activities

---

### User Story 3 - Adapt Schedule for Unexpected Changes (Priority: P3)

A user encounters an unexpected obstruction (illness, work commitment, travel, injury) that prevents them from following their scheduled workout or meal plan. They can inform the AI about the change, and the AI intelligently reschedules their plan to accommodate the disruption while keeping them on track toward their goal. The AI can also suggest rest days when needed.

**Why this priority**: This addresses a major pain point mentioned in the feature description - "not sure of unexpected obstructions or what days off you will need." This makes the plan flexible and realistic, preventing users from abandoning it when life gets in the way.

**Independent Test**: Can be tested by having a user with an active plan report an unexpected event (e.g., "I'm sick today", "I have to travel for work next week"), and verifying that the AI intelligently adjusts the schedule, potentially extending the timeline or redistributing workouts.

**Acceptance Scenarios**:

1. **Given** a user has scheduled workouts for today, **When** they tell the AI "I can't work out today because I'm sick", **Then** the AI acknowledges the situation, suggests rest, and reschedules missed workouts to future dates
2. **Given** a user needs to skip multiple days, **When** they inform the AI about upcoming travel or commitments, **Then** the AI adjusts the schedule for that period and recalculates the plan timeline if needed
3. **Given** a user has been training intensively, **When** the AI detects high consecutive workout days, **Then** the AI may proactively suggest adding a rest day to prevent overtraining
4. **Given** the plan timeline has been extended due to disruptions, **When** the user views the plan, **Then** they can see the updated end date and understand how the goal timeline has shifted

---

### User Story 4 - Update and Refine Plan via AI Suggestions (Priority: P4)

A user who has been following their plan for a while wants to improve or adjust it. They can have a conversation with the AI to request modifications (e.g., "I want to add more cardio", "I'm getting bored with these meals", "This workout is too hard"). The AI can also proactively suggest improvements based on the user's progress and adherence patterns.

**Why this priority**: This enables continuous improvement and prevents stagnation. The AI acts as a virtual fitness coach, helping users optimize their plan over time. This addresses the feature requirement for "ideating new ways to improve things."

**Independent Test**: Can be tested by having a user with progress history request plan modifications through conversation, and verifying that the AI understands the request and updates the plan appropriately while maintaining goal alignment.

**Acceptance Scenarios**:

1. **Given** a user wants to modify their plan, **When** they start a conversation requesting changes (e.g., "add more protein to my meals"), **Then** the AI understands the request and updates the relevant portion of the plan
2. **Given** a user has been following the plan consistently, **When** the AI analyzes progress patterns, **Then** the AI may suggest optimizations like increasing workout intensity or adjusting calorie targets
3. **Given** a user struggles with certain exercises, **When** they mention difficulty to the AI, **Then** the AI suggests alternative exercises or modifications that target the same muscle groups
4. **Given** a user's circumstances change (e.g., new equipment access, schedule change), **When** they inform the AI, **Then** the plan is updated to take advantage of new opportunities or accommodate new constraints
5. **Given** a user achieves their initial goal, **When** they complete the plan, **Then** the AI prompts them to set a new goal and can build upon their progress with a progressive plan

---

### User Story 5 - Multi-Phase Long-Term Plans (Priority: P5)

A user with an ambitious long-term goal (e.g., "compete in a triathlon in 18 months", "transform my fitness over 2 years") creates a multi-phase fitness plan. Each phase has distinct focus areas (e.g., Phase 1: Build base endurance, Phase 2: Increase strength, Phase 3: Peak performance). The user can see their current phase, understand the progression, and track milestone achievements as they move through phases.

**Why this priority**: This serves advanced users with complex goals requiring periodization and progressive training. While less common than simple plans, it demonstrates the application's capability to handle sophisticated training methodologies. This is lower priority because the MVP can function with single-phase plans first.

**Independent Test**: Can be tested by creating a long-term goal requiring multiple phases, verifying that the AI creates distinct phases with different focuses, and that the user can progress through phases over time with clear milestone markers.

**Acceptance Scenarios**:

1. **Given** a user describes a long-term goal requiring progression, **When** the AI creates the plan, **Then** the plan is divided into logical phases with clear objectives for each phase
2. **Given** a user is in Phase 1 of a multi-phase plan, **When** they complete Phase 1 objectives, **Then** the system transitions them to Phase 2 with a clear explanation of what changes and why
3. **Given** a multi-phase plan, **When** the user views plan structure, **Then** they can see all phases, current phase position, and estimated duration of each phase
4. **Given** a user completes a phase milestone, **When** the system registers this achievement, **Then** the user receives recognition and can see their progress toward the ultimate goal

---

### Edge Cases

- What happens when a user stops using the application for an extended period (e.g., 2+ weeks) and returns? → System detects inactivity and initiates AI conversation to reassess current state, offering to resume with adjustments, restart current phase, or create new plan while preserving historical data
- How does the system handle conflicting user requests (e.g., "I want to lose weight but also build significant muscle")? → AI agent educates user on realistic expectations, suggests body recomposition approach (slight calorie deficit with high protein), or helps prioritize primary goal
- What happens when a user's goal becomes unrealistic given their available time and adherence patterns? → AI proactively detects low adherence (< 60% for 3+ weeks), initiates conversation to adjust timeline, reduce frequency, or simplify plan
- How does the system respond when a user reports an injury that affects certain types of exercises? → AI conversation captures injury details, excludes affected movements, suggests rehabilitation exercises, adjusts intensity for impacted muscle groups (uses exercise alternatives from curated database)
- What happens when a user completes their fitness goal ahead of schedule? → AI celebrates achievement, prompts user to set new goal (progression or maintenance), offers to create follow-up plan building on progress
- How does the system handle users who repeatedly skip the same types of workouts or meals? → AI detects pattern (3+ skips of same type), proactively suggests alternatives via conversation (FR-023, FR-024), adjusts plan to user preferences
- What happens when a user wants to maintain their current fitness level rather than progress toward a new goal? → System supports maintenance mode: AI generates plan with stable intensity/volume, focuses on consistency over progression, adjusts calories to maintenance level
- How does the system accommodate users with dietary restrictions (allergies, vegetarian, vegan, religious restrictions)? → Captured during onboarding (FR-030, FR-033), stored in user profile, AI filters meal suggestions to respect restrictions, USDA API enables ingredient-level filtering
- What happens when a user travels to a different time zone or location without equipment access? → User reports travel as disruption event (FR-016), AI adjusts schedule for timezone, suggests bodyweight/hotel gym alternatives based on available equipment, may reduce frequency during travel period

## Requirements *(mandatory)*

### Functional Requirements

**Plan Creation & Management**

- **FR-001**: System MUST enable users to create a fitness plan through conversational interaction with an AI agent
- **FR-002**: System MUST generate fitness plans that include both workout routines and meal plans
- **FR-003**: System MUST support fitness plans for any goal type (weight loss, muscle gain, endurance, general health, event preparation)
- **FR-004**: System MUST support fitness plans of any duration (from weeks to multi-year pursuits)
- **FR-005**: System MUST support multi-phase plans with distinct objectives for each phase
- **FR-006**: System MUST persist user fitness plans and allow retrieval across sessions
- **FR-007**: Users MUST be able to view their complete fitness plan structure including all phases, workouts, and meals
- **FR-008**: Users MUST be able to modify their fitness plan through conversation with the AI agent

**Scheduling & Tracking**

- **FR-009**: System MUST maintain a daily schedule that follows the user's workout and meal plan
- **FR-010**: System MUST display the current day's scheduled workouts and meals
- **FR-011**: System MUST allow users to view upcoming schedule for at least 14 days in advance
- **FR-012**: Users MUST be able to mark workouts and meals as complete
- **FR-013**: System MUST track completion history and calculate adherence statistics
- **FR-014**: System MUST automatically advance the schedule as days progress
- **FR-015**: System MUST track user's current position within their fitness plan (current phase, current week, etc.)

**Adaptability & Rescheduling**

- **FR-016**: System MUST allow users to report unexpected obstructions (illness, travel, commitments) through conversation
- **FR-017**: System MUST intelligently reschedule workouts and meals when disruptions occur
- **FR-018**: System MUST adjust plan timelines when significant schedule changes occur
- **FR-019**: System MUST support manual rest day insertion by user request
- **FR-020**: System MUST prevent harmful overtraining by suggesting rest when appropriate
- **FR-059**: System MUST detect when a user returns after 14+ days of inactivity
- **FR-060**: When returning after extended absence, system MUST initiate AI conversation to reassess user's current fitness level, available time, and whether original goals are still relevant
- **FR-061**: AI MUST offer options to resume existing plan (with adjustments), restart current phase, or create a new plan based on reassessment conversation
- **FR-062**: System MUST preserve all historical progress data even when plans are modified or restarted

**AI Interaction & Suggestions**

- **FR-021**: System MUST support natural language conversation for all user interactions
- **FR-022**: System MUST ask clarifying questions when user input is ambiguous or insufficient
- **FR-023**: System MUST provide exercise alternatives when users report difficulty or boredom
- **FR-024**: System MUST suggest meal variations to prevent dietary monotony
- **FR-025**: System MUST analyze user progress and adherence patterns to suggest plan improvements
- **FR-026**: System MUST guide users to set realistic, measurable fitness goals
- **FR-027**: System MUST provide explanations for plan structure, phase transitions, and recommendations

**AI Orchestration & Architecture**

- **FR-063**: System MUST implement multi-agent orchestration framework with specialized agents: Conversation Agent (user interaction), Fitness Plan Agent (plan coordination), Workout Plan Agent (exercise selection), Meal Plan Agent (nutrition planning)
- **FR-064**: Workout Plan Agent and Meal Plan Agent MUST run simultaneously in parallel when generating plans (independent tasks)
- **FR-065**: System MUST use Redis for ephemeral state storage (conversation context, intermediate results) and PostgreSQL for persistent data
- **FR-066**: AI agents MUST receive storage references (IDs) instead of full data objects to manage context window efficiently
- **FR-067**: System MUST generate fitness plans asynchronously using background workers
- **FR-068**: System MUST stream real-time progress updates to users during plan generation (e.g., "Creating workout schedule...", "Calculating nutrition targets...")
- **FR-069**: Users MUST be able to navigate away during plan generation and return later
- **FR-070**: System MUST send notifications when background plan generation completes
- **FR-071**: Conversation Agent MUST extract and pass only relevant information to specialist agents (not full conversation history)

**Nutrition Data Integration**

- **FR-044**: System MUST integrate with USDA FoodData Central API to access authoritative nutrition data for 300K+ foods
- **FR-045**: AI MUST generate meal suggestions by combining USDA food items with calculated portions to meet user's calorie and macronutrient targets
- **FR-046**: System MUST display nutritional information (calories, protein, carbs, fat) for all suggested meals
- **FR-047**: System MAY support offline meal generation by optionally downloading USDA database locally (POST-MVP: requires ~2GB local storage and periodic sync mechanism)

**Exercise Database**

- **FR-048**: System MUST maintain a curated database of 200-500 common exercises with standardized attributes
- **FR-049**: Each exercise MUST include target muscle groups, required equipment, difficulty level, and recommended alternatives
- **FR-050**: AI MUST select exercises from the curated database when generating workout plans based on user's equipment access and fitness level
- **FR-051**: System MUST support exercise variations (e.g., beginner/intermediate/advanced progressions) within the database

**User Information & Preferences**

- **FR-028**: System MUST collect and store user fitness goals
- **FR-029**: System MUST collect and store user current fitness level and capabilities
- **FR-030**: System MUST collect and store user dietary preferences and restrictions
- **FR-031**: System MUST collect and store user available time and schedule constraints
- **FR-032**: System MUST collect and store user equipment access and location constraints
- **FR-033**: System MUST respect user dietary restrictions (allergies, lifestyle choices, religious requirements)
- **FR-034**: System MUST accommodate users with varying equipment access (home, gym, minimal equipment)

**Progress & Milestones**

- **FR-035**: System MUST track progress toward fitness goals
- **FR-036**: System MUST recognize phase completion in multi-phase plans
- **FR-037**: System MUST celebrate milestone achievements
- **FR-038**: System MUST support goal completion and prompt for new goal setting
- **FR-039**: System MUST maintain historical data showing user's fitness journey over time

**Data Persistence & User Management**

- **FR-040**: System MUST authenticate users to protect personal fitness data
- **FR-041**: System MUST persist all user data (plans, schedules, progress, preferences) across sessions
- **FR-042**: System MUST allow users to access their data from multiple devices
- **FR-043**: System MUST handle users returning after extended absences gracefully

**Authentication & Security**

- **FR-052**: System MUST support user registration with email and password
- **FR-053**: System MUST securely hash passwords using industry-standard algorithms (bcrypt, Argon2)
- **FR-054**: System MUST issue JWT (JSON Web Tokens) upon successful authentication
- **FR-055**: System MUST validate JWT tokens on all protected API endpoints
- **FR-056**: System MUST support token refresh mechanism to maintain user sessions
- **FR-057**: System MUST enforce password complexity requirements (minimum 8 characters, at least 1 uppercase letter, 1 lowercase letter, 1 number, 1 special character)
- **FR-058**: JWT tokens MUST include user ID, email, and expiration timestamp

### Key Entities

- **User**: Represents an individual using the application; attributes include email (unique), password hash (bcrypt/Argon2), JWT refresh token, profile information (current fitness level, goals, preferences), dietary restrictions, equipment access, schedule constraints, account creation timestamp, last login timestamp
- **Fitness Plan**: Represents a complete plan to achieve a fitness goal; attributes include goal description, duration, start date, target end date, current status, overall structure; contains workout plan and meal plan; may contain multiple phases
- **Phase**: Represents a distinct period within a multi-phase plan; attributes include phase number, name, objectives, duration, start date, end date; contains phase-specific workouts and meals
- **Workout Plan**: Component of a fitness plan defining exercise routines; attributes include workout frequency, rest days, progression strategy; contains individual workouts
- **Workout**: Represents a single workout session; attributes include name, target date, exercises, duration, intensity level, completion status, notes
- **Exercise**: Represents an exercise from curated database; attributes include exercise ID, name, description, target muscle groups (primary/secondary), required equipment, difficulty level (beginner/intermediate/advanced), sets, reps, duration, rest period, alternative exercise IDs, instruction notes, video/image reference
- **Meal Plan**: Component of a fitness plan defining nutrition strategy; attributes include calorie targets, macronutrient distribution, meal frequency; contains individual meals
- **Meal**: Represents a single meal instance; attributes include meal type (breakfast, lunch, dinner, snack), target date/time, food items (from USDA FoodData Central), portion sizes, nutritional information (calories, macros), completion status
- **Food Item**: Represents a food from USDA FoodData Central; attributes include FDC ID, description, serving size, nutritional data (calories, protein, carbs, fat, micronutrients)
- **Schedule**: Represents the user's day-to-day timeline of workouts and meals; attributes include current date, scheduled items, completion tracking, upcoming items; links workouts and meals to specific dates
- **Progress Record**: Represents historical tracking data; attributes include date, completed workouts, completed meals, adherence rate, measurements, notes, milestones achieved
- **Conversation**: Represents interaction history between user and AI agent; attributes include timestamp, messages, context, intent, action taken; enables continuous conversational experience
- **Disruption Event**: Represents an unexpected obstruction reported by user; attributes include type (illness, travel, injury, commitment), start date, duration, affected activities, resolution (how schedule was adjusted)
- **Plan Generation Job**: Represents asynchronous plan generation task; attributes include job ID, user ID, status (queued/in-progress/completed/failed), progress percentage, progress message, started timestamp, completed timestamp, result reference (fitness plan ID when complete)
- **Agent Context Reference**: Represents data stored in Redis/PostgreSQL referenced by storage ID; attributes include reference ID, data type (user_profile/conversation_summary/plan_parameters), storage location (Redis key or PostgreSQL table/row), expiration (for Redis), created timestamp

## Success Criteria *(mandatory)*

### Measurable Outcomes

**User Onboarding & Plan Creation**

- **SC-001**: Users can create their first fitness plan in under 10 minutes through conversational interaction
- **SC-002**: 90% of users successfully generate a complete fitness plan (with both workout and meal components) on their first attempt
- **SC-003**: Plan generation begins within 2 seconds with visible progress updates; complete plans delivered within 30 seconds for 90% of cases (users can navigate away and receive notification when ready)

**Daily Usage & Engagement**

- **SC-004**: Users can view today's workout and meal schedule within 3 seconds of opening the application
- **SC-005**: Users can mark a workout or meal as complete in under 5 seconds
- **SC-006**: 70% of users return to the application at least 3 times per week during active plan periods
- **SC-007**: Users spend less than 5 minutes per day on schedule management and tracking

**Schedule Adaptability**

- **SC-008**: Users can report a disruption and receive an adjusted schedule within 1 minute of the conversation
- **SC-009**: 85% of users who report disruptions continue following their plan after the adjustment
- **SC-010**: Schedule adjustments maintain goal achievability in 95% of cases (accounting for timeline extensions)

**Plan Quality & Effectiveness**

- **SC-011**: Generated fitness plans align with established fitness principles and safety guidelines in 100% of cases
- **SC-012**: Multi-phase plans show logical progression with distinct objectives in each phase
- **SC-013**: Users rate their fitness plan as "relevant to my goals" with an average score of 4.0 or higher out of 5.0
- **SC-014**: 60% of users who complete their initial plan create a new follow-up plan

**AI Interaction Quality**

- **SC-015**: AI understands user intent correctly in 90% of conversational interactions
- **SC-016**: AI provides relevant exercise alternatives when requested in 95% of cases
- **SC-017**: Users can modify their plan through conversation in under 3 minutes
- **SC-018**: AI explanations and recommendations are rated as "helpful" by 80% of users

**System Performance & Reliability**

- **SC-019**: Application supports 1000 concurrent users without performance degradation
- **SC-020**: Schedule data synchronizes across devices within 5 seconds
- **SC-021**: System maintains 99.5% uptime during peak usage hours (6 AM - 10 PM local time)
- **SC-022**: All user data persists reliably with zero data loss incidents
- **SC-027**: Parallel agent execution (Workout Plan Agent + Meal Plan Agent) reduces total plan generation time by 40% compared to sequential processing

**Time Savings & Value**

- **SC-023**: Users report saving at least 2 hours per week on fitness planning and schedule management compared to manual methods
- **SC-024**: 75% of users achieve measurable progress toward their fitness goals within the first 4 weeks
- **SC-025**: Users who follow their plan for 8+ weeks show 50% better adherence rates compared to self-managed fitness plans
- **SC-026**: 80% of users report reduced stress and decision fatigue around fitness planning
