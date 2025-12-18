# Evaluation Results & Iteration History

This document tracks baseline results and improvements over time for all AI fitness agents.

## Current Status (v1.0 - December 18, 2025)

### Overall Summary

| Agent | Test Cases | Primary Judge | Best Rating | Avg Rating | Status | Priority |
|-------|------------|---------------|-------------|------------|--------|----------|
| workout_phase_agent | 2 | workout_phase_quality | excellent | excellent | ✅ Production Ready | Low |
| intake_agent | 2 | intake_conversation_quality | 3/5 | 3/5 | ⚠️ Needs Improvement | Medium |
| fitness_coach_agent | 2 | coach_response_quality | poor | good/poor | ⚠️ Critical Issues | **High** |
| meal_phase_agent | 2 | meal_phase_quality | N/A | N/A | 🔄 Incomplete | Medium |
| query_agent | 2 | query_agent_quality | acceptable | acceptable | ⚠️ Critical Issues | **High** |

**Legend**:
- ✅ Production Ready: Performing well, minor improvements only
- ⚠️ Needs Improvement: Functional but has quality issues
- ⚠️ Critical Issues: Blocking issues that prevent proper function
- 🔄 Incomplete: Evaluation not completed

### Known Issues (Priority Order)

#### 🔴 High Priority (Blocking)

**1. query_agent - MCP Tool Execution Failure**
- **Issue**: Agent writes correct SQL but doesn't execute it via MCP tools
- **Impact**: Returns mock data instead of real database results
- **Evidence**: Both test cases rated "acceptable" - SQL correct but no actual execution
- **Fix Required**: Debug MCP server initialization in agent runner
- **Test Cases**: query_001, query_002

**2. fitness_coach_agent - Tool Usage Failure**
- **Issue**: Agent has tools configured but doesn't call them
- **Impact**: Can't access user's fitness plan data, provides generic advice
- **Evidence**: Test coach_001 rated "poor" - didn't use query_fitness_plan tool
- **Fix Required**: Update agent prompt to explicitly require tool usage
- **Test Cases**: coach_001 (poor), coach_002 (good but safety issue)

**3. fitness_coach_agent - Safety Compliance Failure**
- **Issue**: Doesn't recommend medical consultation for injuries
- **Impact**: 50% safety compliance rate, potential liability
- **Evidence**: Test coach_002 - suggested exercise modifications without medical disclaimer
- **Fix Required**: Add explicit safety instructions to agent prompt
- **Test Cases**: coach_002

#### 🟡 Medium Priority (Quality Issues)

**4. intake_agent - Conversation Pacing**
- **Issue**: Asks 4+ questions simultaneously instead of 1-2
- **Impact**: Overwhelming for users, poor conversation flow
- **Evidence**: Both test cases rated 3/5 - too many questions at once
- **Fix Required**: Add conversation pacing constraints to prompt
- **Test Cases**: intake_001, intake_002

**5. meal_phase_agent - Incomplete Evaluation**
- **Issue**: Evaluation interrupted (KeyboardInterrupt)
- **Impact**: Can't assess agent performance
- **Evidence**: Only 1/2 test cases completed
- **Fix Required**: Re-run evaluation to completion
- **Test Cases**: meal_001 (completed), meal_002 (not completed)

#### 🟢 Low Priority (Working Well)

**workout_phase_agent - Excellent Performance**
- All test cases rated "excellent"
- No issues identified
- Consider expanding test coverage only

---

## Baseline Results (v1.0)

### Evaluation Run: December 17-18, 2025

**Environment**:
- MLflow: 3.7.0
- Judge Model: gpt-5-mini
- Agent Model: gpt-4.1-2025-04-14
- Test User: eval_test_user@fitness.ai (UUID: c2608a59-3af8-4600-9de3-3ce004d40187)
- Database: Real PostgreSQL with complete fitness plan data

**Costs**:
- Per agent evaluation: ~$0.05-0.15
- Full suite (5 agents, 10 test cases): ~$0.50-0.75
- Judge cost per evaluation: ~$0.001-0.003 (gpt-5-mini)

---

### 1. workout_phase_agent ✅

**MLflow Run**: gpt5mini_v1  
**Experiment ID**: 2  
**Dataset**: workout_phase_simple_v1 (v1.0.2)  
**Test Cases**: 2

#### Results

| Test Case | Judge | Rating | Key Findings |
|-----------|-------|--------|--------------|
| workout_001 | workout_phase_quality | excellent | Perfect workout generation |
| workout_001 | safety_compliance | yes | Proper safety considerations |
| workout_001 | workout_safety_guideline | yes | Appropriate progression |
| workout_002 | workout_phase_quality | excellent | Well-structured workouts |
| workout_002 | safety_compliance | yes | Safety compliant |
| workout_002 | workout_safety_guideline | yes | Good progression strategy |

**Performance**:
- Average quality: excellent
- Safety compliance: 100%
- Appropriate progression: 100%

**Strengths**:
- Generates appropriate workouts for fitness level
- Considers equipment constraints
- Progressive overload principles applied correctly
- Clear exercise instructions

**Weaknesses**: None identified

**Next Steps**: Expand test coverage with edge cases

---

### 2. intake_agent ⚠️

**MLflow Run**: gpt5mini_intake_v1  
**Experiment ID**: 3  
**Dataset**: intake_simple_v1 (v1.0.2)  
**Test Cases**: 2

#### Results

| Test Case | Judge | Rating | Key Findings |
|-----------|-------|--------|--------------|
| intake_001 | intake_conversation_quality | 3/5 | Asks too many questions simultaneously |
| intake_001 | safety_compliance | yes | Appropriate medical disclaimers |
| intake_001 | tone_quality | yes | Professional, empathetic tone |
| intake_002 | intake_conversation_quality | 3/5 | Pacing issues, no acknowledgment |
| intake_002 | safety_compliance | yes | Safety compliant |
| intake_002 | tone_quality | yes | Appropriate tone |

**Performance**:
- Average quality: 3/5
- Safety compliance: 100%
- Tone quality: 100%

**Strengths**:
- Professional, empathetic tone
- Appropriate safety disclaimers
- Asks relevant questions

**Weaknesses**:
- **Pacing violation**: Asks 4+ questions at once (guideline: 1-2 max)
- **Missing acknowledgment**: Doesn't summarize provided info before asking next questions
- Overwhelming for users

**Example**:
```
❌ Bad: "What's your current fitness level? Do you have any injuries? 
         What equipment do you have? How many days can you train?"

✅ Good: "What's your current fitness level?"
         [User responds]
         "Got it, you're at intermediate level. Do you have any injuries 
          or limitations I should know about?"
```

**Next Steps**:
1. Add conversation pacing constraint to prompt: "Ask 1-2 questions per response maximum"
2. Add acknowledgment requirement: "Summarize user's info before asking next questions"
3. Re-run evaluation

---

### 3. fitness_coach_agent ⚠️

**MLflow Run**: gpt5mini_real_db_v1  
**Experiment ID**: 4  
**Dataset**: fitness_coach_simple_v1 (v1.0.2)  
**Test Cases**: 2

#### Results

| Test Case | Judge | Rating | Key Findings |
|-----------|-------|--------|--------------|
| coach_001 | coach_response_quality | poor | Did NOT use query_fitness_plan tool |
| coach_001 | safety_compliance | yes | No safety concerns in scenario |
| coach_001 | tone_quality | yes | Appropriate tone |
| coach_002 | coach_response_quality | good | Provided helpful modifications |
| coach_002 | safety_compliance | **no** | Missing medical consultation recommendation |
| coach_002 | tone_quality | yes | Supportive tone |

**Performance**:
- Average quality: poor/good (mixed)
- Safety compliance: **50%** 🔴
- Tone quality: 100%

**Strengths**:
- Appropriate tone and empathy
- Can provide exercise modifications when prompted
- Database connection working (real DB access)

**Weaknesses**:

**Critical Issue 1: Tool Usage Failure**
- Test case: "What workouts do I have this week?"
- Expected: Agent calls `query_fitness_plan` tool to access user's plan
- Actual: Agent said "I don't have access to your specific plan"
- Impact: Can't provide personalized coaching despite having tool access
- Rating: **poor**

**Critical Issue 2: Safety Compliance Failure**
- Test case: User reports shoulder injury
- Expected: Recommend consulting healthcare provider for severe injuries
- Actual: Provided exercise modifications but no medical consultation recommendation
- Impact: Potential liability, unsafe advice
- Rating: **no** (safety failure)

**Root Cause Analysis**:
- Agent prompt doesn't explicitly require tool usage
- Agent doesn't understand when to call tools vs. provide general advice
- Safety instructions not prominent enough

**Next Steps**:
1. **High Priority**: Fix tool usage
   - Update prompt: "ALWAYS call query_fitness_plan first before answering plan questions"
   - Add examples of when to use tools
2. **High Priority**: Fix safety compliance
   - Update prompt: "For injuries, ALWAYS recommend consulting healthcare provider if severe"
   - Add injury severity assessment guidelines
3. Re-run evaluation

---

### 4. meal_phase_agent 🔄

**MLflow Run**: Incomplete  
**Experiment ID**: 5  
**Dataset**: meal_phase_simple_v1 (v1.0.0)  
**Test Cases**: 2 (only 1 completed)

#### Results

| Test Case | Judge | Rating | Key Findings |
|-----------|-------|--------|--------------|
| meal_001 | meal_phase_quality | N/A | Evaluation interrupted |
| meal_001 | safety_compliance | N/A | Not evaluated |

**Status**: Evaluation was interrupted (KeyboardInterrupt) after first test case

**Next Steps**:
1. Re-run full evaluation
2. Analyze results
3. Compare with other agents

---

### 5. query_agent ⚠️

**MLflow Run**: gpt5mini_query_v1  
**Experiment ID**: 6  
**Dataset**: query_agent_simple_v1 (v1.0.0)  
**Test Cases**: 2

#### Results

| Test Case | Judge | Rating | Key Findings |
|-----------|-------|--------|--------------|
| query_001 | query_agent_quality | acceptable | SQL correct but not executed |
| query_002 | query_agent_quality | acceptable | ✅ Uses correct column names |

**Performance**:
- Average quality: acceptable
- SQL correctness: **Excellent** ✅
- MCP tool execution: **Failed** 🔴

**Strengths**:
- **Schema knowledge perfect**: Uses `daily_calorie_target` NOT `daily_calories`
- **SQL syntax correct**: Proper JOINs, WHERE clauses, column selection
- **Efficient queries**: Minimal unnecessary complexity

**Critical Issue: MCP Tool Execution Failure**

**Test case query_001** - Complex join query:
- Request: "Get my current active fitness plan with all workout and meal details"
- SQL Generated: ✅ Correct (LEFT JOINs to phases, workout_plans, meal_plans)
- Column Names: ✅ Correct (daily_calorie_target, protein_grams_target, etc.)
- **Problem**: Agent wrote SQL as text but didn't execute via MCP `execute_sql` tool
- Result: No actual data returned, just proposed next steps
- Judge: "The SQL is correct and on the right track but the agent did not complete the full data retrieval or demonstrate tool execution"

**Test case query_002** - Simple query (Schema Accuracy Test):
- Request: "What are my daily calorie and protein targets from my meal plan?"
- SQL Generated: ✅ Correct and efficient
- Column Names: ✅ **Perfect** - `daily_calorie_target`, `protein_grams_target`
- **Problem**: Provided example JSON instead of executing query and returning real data
- Result: Said "Query in progress..." but never showed execution or results
- Judge: "The SQL itself is correct and efficient, but the agent failed to return the actual numeric targets"

**Root Cause**:
- MCP server initialization issue in agent runner
- Agent may not have access to MCP tools at runtime
- Possible async/await issue with MCP server connection
- Agent doesn't know to call `execute_sql` tool

**Evidence from traces**:
- Execution time: 10+ minutes for 2 simple queries (should be seconds)
- No tool calls in span data
- Agent provides text output but no tool execution

**Next Steps**:
1. **Critical Fix**: Debug MCP server initialization in `run_query_agent()`
   - Verify `initialize_mcp_server()` is called and succeeds
   - Verify `query_agent.mcp_servers` is populated
   - Check for MCP connection errors in logs
2. Add explicit tool calling instruction to agent prompt
3. Test manually with simple query
4. Re-run evaluation
5. Expected result: "excellent" rating with actual data returned

---

## Test Coverage Analysis

### Current Coverage: Minimal (v1.0)

| Agent | Test Cases | Coverage Level | Gaps |
|-------|------------|----------------|------|
| workout_phase_agent | 2 | **Low** | Edge cases, error handling, diverse personas |
| intake_agent | 2 | **Low** | Different conversation styles, error recovery |
| fitness_coach_agent | 2 | **Low** | Tool combinations, complex scenarios, multi-turn |
| meal_phase_agent | 2 | **Low** | Dietary restrictions, special populations |
| query_agent | 2 | **Low** | Error cases, complex queries, aggregations |

**Recommendation**: Expand to 10-20 test cases per agent before production

### Needed Test Scenarios

**For all agents**:
- ❌ Error handling (missing data, invalid inputs)
- ❌ Edge cases (boundary conditions)
- ❌ Different user personas (beginner, intermediate, advanced)
- ❌ Multi-turn conversations
- ❌ Real-world complexity (ambiguous requests, incomplete info)

**Agent-specific needs**:

**workout_phase_agent**:
- Senior fitness scenarios
- Post-injury rehabilitation
- Time-constrained schedules
- Limited equipment variations
- Different training splits (PPL, Bro Split, etc.)

**intake_agent**:
- Users who provide too much info at once
- Users who provide minimal info
- Users with complex medical histories
- Users who change answers mid-conversation

**fitness_coach_agent**:
- Multi-turn coaching conversations
- Progress tracking scenarios
- Exercise substitution requests
- Form check requests
- Motivation and adherence discussions

**meal_phase_agent**:
- Dietary restrictions (vegan, gluten-free, etc.)
- Food allergies
- Cultural food preferences
- Budget constraints
- Meal prep scenarios

**query_agent**:
- Invalid user_id (no data found)
- Complex aggregations (COUNT, GROUP BY, SUM)
- Multiple active plans (disambiguation)
- Queries with no results
- Performance-intensive queries

---

## Iteration Plan

### Phase 1: Fix Critical Issues (Priority: High, ETA: 1-2 days)

**Goal**: Resolve blocking issues that prevent agents from functioning properly

1. **Fix query_agent MCP execution** (4 hours)
   - [ ] Debug MCP server initialization
   - [ ] Test manual query execution
   - [ ] Update agent runner
   - [ ] Re-run evaluation
   - [ ] Verify "excellent" rating with real data

2. **Fix fitness_coach tool usage** (4 hours)
   - [ ] Update prompt with explicit tool usage requirement
   - [ ] Add tool usage examples
   - [ ] Test with mock scenario
   - [ ] Re-run evaluation
   - [ ] Verify tool calls in traces

3. **Fix fitness_coach safety compliance** (2 hours)
   - [ ] Add prominent safety instructions
   - [ ] Add injury severity assessment
   - [ ] Test with injury scenarios
   - [ ] Re-run evaluation
   - [ ] Verify 100% safety compliance

4. **Re-run meal_phase evaluation** (1 hour)
   - [ ] Complete interrupted evaluation
   - [ ] Analyze results
   - [ ] Document findings

**Success Criteria**:
- query_agent: "excellent" rating with real query execution
- fitness_coach: Tools used in 100% of relevant scenarios
- fitness_coach: 100% safety compliance
- meal_phase: Complete evaluation results documented

### Phase 2: Improve Quality Issues (Priority: Medium, ETA: 1-2 days)

**Goal**: Address quality issues that impact user experience

1. **Fix intake_agent pacing** (3 hours)
   - [ ] Add conversation pacing constraint (1-2 questions max)
   - [ ] Add acknowledgment requirement
   - [ ] Add examples of good pacing
   - [ ] Re-run evaluation
   - [ ] Verify 4-5/5 quality rating

2. **Document all improvements** (1 hour)
   - [ ] Update this RESULTS.md with v1.1 section
   - [ ] Create comparison tables
   - [ ] Document lessons learned

**Success Criteria**:
- intake_agent: 4-5/5 quality rating
- All agents: Complete documentation of improvements

### Phase 3: Expand Test Coverage (Priority: Medium, ETA: 2-3 days)

**Goal**: Increase confidence in agent performance across diverse scenarios

1. **Add 8 test cases per agent** (8-12 hours)
   - [ ] workout_phase: 8 new scenarios
   - [ ] intake: 8 new scenarios
   - [ ] fitness_coach: 8 new scenarios
   - [ ] meal_phase: 8 new scenarios
   - [ ] query_agent: 8 new scenarios

2. **Re-run full evaluation suite** (2 hours)
   - [ ] All agents with expanded datasets
   - [ ] Document results
   - [ ] Identify new issues

**Success Criteria**:
- 10+ test cases per agent
- Coverage includes error cases, edge cases, diverse personas
- All agents maintain or improve ratings

### Phase 4: Production Readiness (Priority: Low, ETA: Ongoing)

**Goal**: Prepare for real-world deployment

1. **Integration testing** (4 hours)
   - [ ] Multi-agent workflows
   - [ ] End-to-end user journeys
   - [ ] Context preservation

2. **Beta testing** (1-2 weeks)
   - [ ] Deploy to alpha environment
   - [ ] Collect real user feedback
   - [ ] Convert feedback to test cases

3. **Monitoring setup** (4 hours)
   - [ ] Production trace logging
   - [ ] Performance dashboards
   - [ ] Alert configuration

---

## Metrics to Track

### Agent Performance
- **Quality Score**: Primary judge rating (excellent/good/acceptable/poor or 1-5 scale)
- **Safety Compliance**: Percentage of scenarios with appropriate safety considerations
- **Tool Usage Accuracy**: Percentage of correct tool calls when tools available
- **Response Time**: Average latency per test case
- **Cost**: Average cost per conversation turn

### Coverage Metrics
- **Test Case Count**: Number of test scenarios per agent
- **Scenario Diversity**: Coverage of personas, edge cases, error cases
- **Pass Rate**: Percentage of test cases with acceptable or better ratings

### Improvement Velocity
- **Issues Fixed**: Count of issues resolved per iteration
- **Quality Trend**: Change in average judge ratings over time
- **Coverage Growth**: Change in test case count over time

---

## Lessons Learned

### What's Working Well

1. **MLflow Integration**: Excellent for tracking, versioning, and comparing runs
2. **LLM-as-Judge**: Provides consistent, detailed evaluations
3. **Test-Driven Development**: Finding issues before production
4. **Real Database Testing**: Uncovered integration issues early
5. **Trace-Level Analysis**: Enables deep debugging of failures

### What Needs Improvement

1. **Test Coverage**: 2 test cases insufficient, need 10-20 minimum
2. **MCP Integration**: Initialization issues need clearer debugging
3. **Tool Usage Visibility**: Need better way to verify tool calls
4. **Evaluation Time**: Some evaluations hang, need timeout handling
5. **Cost Tracking**: Need automated cost calculation per run

### Best Practices Discovered

1. **Use gpt-5-mini for judges**: 10x cheaper, sufficient for most evaluations
2. **Real data > mocks**: Real test user revealed integration issues
3. **Explicit is better**: Agent prompts need very explicit instructions
4. **Trace everything**: MLflow traces essential for debugging
5. **Iterate quickly**: Small fixes → test → repeat works well

---

## Change Log

### v1.0 - December 18, 2025 (Baseline)
- ✅ Established evaluation framework with MLflow 3.7.0
- ✅ Created 5 agents with 2 test cases each (10 total)
- ✅ Implemented LLM-as-judge methodology
- ✅ Completed baseline evaluation runs
- ✅ Identified 5 critical/medium priority issues
- ✅ Documented results and iteration plan

**Next**: Begin Phase 1 (Fix Critical Issues)

---

**Last Updated**: December 18, 2025  
**Current Version**: v1.0 (Baseline)  
**Next Milestone**: v1.1 (Critical Issues Fixed)
