# AI Fitness Agent Evaluation Framework

Comprehensive evaluation system for testing AI fitness agents using MLflow 3.7.0 and LLM-as-judge methodology.

## Overview

This framework enables systematic testing, measurement, and improvement of AI agents through:
- **Structured test datasets** with inputs and expected behaviors
- **LLM judges** that evaluate agent outputs against quality criteria  
- **MLflow tracking** for versioning, comparison, and analysis
- **Trace-level debugging** for understanding failures
- **Iterative improvement** cycle: test → analyze → fix → re-test

## Quick Start

### Run Evaluation for All Agents
```bash
cd backend
uv run python evaluations/run_evaluation.py --agent all --run-name "your_run_name"
```

### Run Evaluation for Specific Agent
```bash
uv run python evaluations/run_evaluation.py --agent workout_phase_agent --run-name "iteration_v2"
```

### View Results
```bash
# MLflow UI (runs on http://localhost:5000)
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns

# Or use MLflow MCP to query traces
uv run mlflow traces search --experiment-id 2 --max-results 10 --output json
```

## Architecture

### Components

```
Evaluation Pipeline:
  Dataset (JSON) → Agent Runner → Agent Execution → Judge Evaluation → MLflow Storage
                                       ↓
                                  MCP Tools / Database
```

**Key Files**:
- `datasets_simple/` - Test case datasets (inputs + expectations)
- `judges.py` - LLM judge definitions with evaluation criteria
- `agent_runners.py` - Wrappers that execute agents with test inputs
- `run_evaluation.py` - Main orchestration script
- `create_mlflow_datasets.py` - Generate dataset JSON files
- `upload_query_agent_dataset.py` - Upload datasets to MLflow

### Agent Coverage

| Agent | Experiment ID | Dataset ID | Test Cases | Status |
|-------|---------------|------------|------------|--------|
| workout_phase_agent | 2 | d-e984081e... | 2 | ✅ Excellent |
| intake_agent | 3 | d-716eb242... | 2 | ⚠️ Pacing issues |
| fitness_coach_agent | 4 | d-c97983c9... | 2 | ⚠️ Tool usage issues |
| meal_phase_agent | 5 | d-e87ebc1a... | 2 | 🔄 Needs re-run |
| query_agent | 6 | d-493cf40b... | 2 | ⚠️ MCP tool execution |

## Creating New Test Cases

### 1. Add Test Case to Dataset

Edit `create_mlflow_datasets.py`:

```python
# Example: Adding test case to workout_phase_dataset
{
    "id": "workout_003",
    "inputs": {
        "workout_plan_description": "Bodyweight training for beginners",
        "phase_number": 1,
        "phase_name": "Foundation",
        # ... other inputs
    },
    "expectations": {
        "expected_behavior": "Generate beginner-friendly bodyweight workouts...",
        "uses_correct_exercise_form": True,
        "appropriate_volume": True,
        # ... other expectations
    },
    "source": {"type": "manual", "author": "dev_team"},
    "tags": {"difficulty": "beginner", "equipment": "none"}
}
```

### 2. Generate Dataset Files

```bash
cd backend
python evaluations/create_mlflow_datasets.py
```

This creates/updates JSON files in `datasets_simple/`.

### 3. Upload to MLflow

```bash
# For query_agent (example)
python evaluations/upload_query_agent_dataset.py

# Note: Other agents may need dataset ID updates in run_evaluation.py
```

### 4. Run Evaluation

```bash
uv run python evaluations/run_evaluation.py --agent workout_phase_agent --run-name "added_test_003"
```

## Creating New Judges

Judges evaluate agent outputs using LLM reasoning. Create in `judges.py`:

```python
from mlflow.genai import make_judge
from typing import Literal

my_custom_judge = make_judge(
    name="my_custom_quality",
    instructions="""
You are evaluating an AI fitness agent.

User Request:
{{ inputs }}

Agent Response:
{{ outputs }}

Expected Behavior:
{{ expectations }}

Evaluate on:
1. **Criterion 1** (40%): Description...
2. **Criterion 2** (30%): Description...
3. **Criterion 3** (30%): Description...

Rate: excellent, good, acceptable, or poor
""",
    feedback_value_type=Literal["excellent", "good", "acceptable", "poor"],
    model="openai:/gpt-5-mini"  # Cost-effective for portfolio project
)

# Add to judge registry
JUDGES["my_custom"] = my_custom_judge

# Add to agent mapping
def get_judges_for_agent(agent_name: str):
    primary_judges = {
        "my_agent": [my_custom_judge],
        # ...
    }
```

### Judge Design Tips

- **Weight criteria**: Most important = highest percentage
- **Be specific**: Concrete examples > vague descriptions
- **Template variables**: Use `{{ inputs }}`, `{{ outputs }}`, `{{ expectations }}`
- **Feedback types**: `Literal[...]` for categories, `int` for scores, `bool` for pass/fail
- **Model choice**: `gpt-5-mini` for speed/cost, `gpt-4` for complex reasoning

## Creating New Agent Runners

Agent runners execute agents with test inputs. Add to `agent_runners.py`:

```python
async def run_my_agent(**inputs) -> dict[str, Any]:
    """Run my_agent with MLflow dataset inputs."""
    # Extract inputs
    user_input = inputs.get("user_input")
    context = inputs.get("context", {})
    
    # Initialize any required services (MCP, database, etc.)
    await initialize_services()
    
    try:
        # Run agent
        result = await Runner.run(
            starting_agent=my_agent,
            input=user_input,
            context=context,
            session=None
        )
        
        # Extract response
        return {
            "response": result.final_output,
            "metadata": {
                "turns": result.turn_count,
                # ... other useful metadata
            }
        }
    finally:
        # Clean up
        await cleanup_services()

def run_my_agent_sync(**inputs) -> dict[str, Any]:
    """Synchronous wrapper for run_my_agent."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(run_my_agent(**inputs))

# Add to registry
AGENT_RUNNERS["my_agent"] = run_my_agent_sync
```

## Analyzing Results

### 1. MLflow UI

Navigate to http://localhost:5000:
- **Experiments** → Select agent experiment
- **Runs** → View evaluation run
- **Metrics** → See judge scores
- **Traces** → Drill into individual executions

### 2. MLflow CLI (with MLflow MCP)

```bash
# Search traces for experiment
uv run mlflow traces search --experiment-id 4 --max-results 10 --output json

# Get specific trace details
uv run mlflow traces get --trace-id tr-abc123def

# Get trace assessments (judge evaluations)
uv run mlflow traces get-assessment --trace-id tr-abc123def --assessment-id asmt-xyz789
```

### 3. Programmatic Analysis

```python
import mlflow
from mlflow.genai.datasets import get_dataset

# Load dataset
dataset = get_dataset(dataset_id="d-493cf40ba48e49c6bfeb96103ef9336f")

# Get run metrics
client = mlflow.tracking.MlflowClient()
run = client.get_run("run_id_here")
metrics = run.data.metrics
```

## Iteration Workflow

### Standard Development Cycle

```
1. Identify Issue
   ↓ (from evaluation results or real usage)
2. Add Test Case
   ↓ (covering the issue scenario)
3. Verify Failure
   ↓ (run eval, confirm agent fails)
4. Fix Agent
   ↓ (update prompt, logic, tools)
5. Re-run Evaluation
   ↓ (verify fix works)
6. Document in RESULTS.md
   ↓ (track improvement)
7. Commit Changes
   ↓ (version control)
8. Deploy to next stage
   (alpha → beta → production)
```

### Example: Fixing query_agent MCP Tool Issue

```bash
# 1. Issue identified: Agent writes SQL but doesn't execute
# 2. Test case already exists: query_002

# 3. Verify current failure
uv run python evaluations/run_evaluation.py --agent query_agent --run-name "before_fix"
# Result: "acceptable" - SQL correct but no execution

# 4. Fix agent (e.g., update runner to properly initialize MCP server)
# Edit: evaluations/agent_runners.py

# 5. Re-run evaluation
uv run python evaluations/run_evaluation.py --agent query_agent --run-name "after_fix"
# Expected: "excellent" - SQL correct AND executed

# 6. Document
echo "## Iteration 2 - Fixed query_agent MCP execution" >> evaluations/RESULTS.md

# 7. Commit
git add backend/evaluations/
git commit -m "Fix query_agent MCP tool execution"

# 8. Deploy (when ready)
```

## Feedback Loop Integration

### Capturing Real-World Feedback

**Option 1: MLflow-based (Current)**
```python
# In your app, log user feedback as MLflow traces
import mlflow

with mlflow.start_run():
    # Log conversation
    mlflow.log_param("user_id", user.id)
    mlflow.log_param("agent", "fitness_coach_agent")
    mlflow.log_text(conversation_text, "conversation.txt")
    
    # Log user feedback
    mlflow.log_metric("user_satisfaction", satisfaction_score)
    mlflow.log_param("feedback_text", user_feedback)
    mlflow.log_param("issue_category", "tool_usage")  # For categorization
```

**Option 2: Simple Ticketing System**
```
backend/feedback/
├── feedback_tracker.py       # Simple ticket management
├── tickets/
│   ├── 001_coach_no_query.json
│   ├── 002_intake_too_many_questions.json
│   └── ...
└── convert_to_test_case.py   # Convert ticket → test case
```

Example ticket format:
```json
{
  "id": "001",
  "date": "2025-12-18",
  "agent": "fitness_coach_agent",
  "issue": "Agent didn't query user's fitness plan",
  "user_input": "What workouts do I have this week?",
  "agent_response": "I don't have access to your plan...",
  "expected_behavior": "Agent should call query_fitness_plan tool",
  "status": "converted_to_test",
  "test_case_id": "coach_003"
}
```

**Option 3: Langfuse Integration (Future)**
- Replace OpenAI traces with Langfuse for local hosting
- Built-in feedback annotation UI
- Automatic test case generation from failures

### Converting Feedback to Test Cases

```bash
# Manual process (for now)
# 1. Review feedback in MLflow or tickets
# 2. Identify pattern/issue
# 3. Add test case to create_mlflow_datasets.py
# 4. Run evaluation to verify issue
# 5. Fix agent
# 6. Re-run evaluation
```

## Monitoring Production

### Current Setup: MLflow Traces
- All agent interactions logged to MLflow
- Traces stored in `backend/mlflow.db`
- Accessible via MLflow UI or MCP

### Future Enhancements

**Real-time Monitoring**:
```python
# Add to agent execution
from datetime import datetime

async def monitored_agent_execution(agent, input, context):
    start = datetime.now()
    
    try:
        result = await Runner.run(agent, input, context)
        
        # Log success metrics
        mlflow.log_metric("latency_ms", (datetime.now() - start).total_seconds() * 1000)
        mlflow.log_metric("success", 1)
        
        return result
    except Exception as e:
        # Log failure
        mlflow.log_metric("success", 0)
        mlflow.log_param("error", str(e))
        raise
```

**Dashboards** (Future):
- Grafana + MLflow for real-time agent performance
- Track: success rate, latency, token usage, costs
- Alerts on degradation

## Cost Tracking

### Current Costs (Estimated)

**Per Evaluation Run**:
- Agent execution: $0.01-0.05 per test case (GPT-4.1)
- Judge evaluation: $0.001-0.003 per judgment (GPT-5-mini)
- Total per agent (2 test cases, 1-2 judges): ~$0.05-0.15
- **Full suite (5 agents)**: ~$0.25-0.75 per run

**Monthly (if running daily)**:
- Development: ~$7.50-$22.50/month
- Production monitoring: Variable based on traffic

**Optimization Tips**:
- Use `gpt-5-mini` for judges (10x cheaper)
- Cache prompt context where possible
- Batch evaluations instead of per-commit
- Use smaller models for simple agents

## Best Practices

### Test Case Design
- ✅ **Cover edge cases**: Not just happy paths
- ✅ **Use real data**: Actual user scenarios > synthetic
- ✅ **Be specific**: Clear expectations > vague goals
- ✅ **Incremental complexity**: Start simple, add difficulty
- ✅ **Diverse personas**: Beginner, intermediate, advanced

### Judge Design
- ✅ **Weight criteria**: Most important = highest percentage
- ✅ **Concrete examples**: Show what good/bad looks like
- ✅ **Avoid ambiguity**: Clear rubrics > subjective judgment
- ✅ **Multiple judges**: Primary (quality) + secondary (safety, tone)
- ✅ **Cheap models**: gpt-5-mini is usually sufficient

### Agent Development
- ✅ **Test-first**: Write test before fixing issue
- ✅ **Iterate quickly**: Small changes → test → repeat
- ✅ **Document learnings**: Track what works in RESULTS.md
- ✅ **Version control**: Commit after each improvement
- ✅ **Regression testing**: Re-run full suite periodically

### Production Readiness
- ✅ **Expand coverage**: 10-20 test cases per agent minimum
- ✅ **Real user validation**: Beta test with actual users
- ✅ **Monitor continuously**: Track production performance
- ✅ **Feedback loop**: Convert failures → test cases
- ✅ **Staged rollout**: Alpha → beta → production

## Troubleshooting

### Evaluation Hangs/Times Out
- Check MCP server initialization in agent_runners.py
- Verify database connection in test environment
- Look for infinite loops in agent logic
- Set timeout limits in Runner.run()

### Judge Gives Inconsistent Ratings
- Add more specific criteria to instructions
- Provide concrete examples of each rating level
- Use multiple judges and aggregate scores
- Consider using structured output (function calling)

### High Evaluation Costs
- Switch judges to gpt-5-mini
- Reduce judge prompt length
- Use simpler evaluation criteria
- Batch test cases when possible

### Can't Reproduce Evaluation Results
- Ensure deterministic temperature (0.0) for agents
- Version datasets and judges in git
- Document environment (Python version, dependencies)
- Use MLflow run IDs for exact reproducibility

## References

- **MLflow Documentation**: https://mlflow.org/docs/latest/index.html
- **MLflow GenAI Evaluation**: https://mlflow.org/docs/latest/llms/llm-evaluate/index.html
- **OpenAI Agents SDK**: https://github.com/openai/openai-python
- **Best Practices**: See RESULTS.md for lessons learned

## Contributing

When adding new agents or test cases:
1. Update this README with new agent entry
2. Add test cases to create_mlflow_datasets.py
3. Create judge in judges.py
4. Create runner in agent_runners.py
5. Update run_evaluation.py with new agent config
6. Run evaluation and document results in RESULTS.md
7. Commit all changes with descriptive message

---

**Last Updated**: December 18, 2025  
**Framework Version**: v1.0  
**MLflow Version**: 3.7.0
