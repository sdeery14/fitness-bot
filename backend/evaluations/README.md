# MLflow Evaluation Framework for AI Fitness Agent

This directory contains the MLflow-based evaluation framework for measuring and improving the AI agents in the fitness-bot project.

## Architecture

```
evaluations/
├── dataset_schema.py          # Pydantic schemas for test cases
├── workout_phase_dataset.py   # Test dataset for workout phase agent (10 test cases)
├── llm_judges.py              # LLM-as-a-judge evaluators (4 judges)
├── custom_metrics.py          # Custom metrics (latency, cost, tool usage)
├── harness.py                 # Main evaluation harness
└── datasets/                  # JSON datasets (generated)

docker/
└── docker-compose.mlflow.yml  # MLflow stack (MLflow + Postgres + MinIO)

mlflow/
├── Dockerfile                 # MLflow server container
├── requirements.txt           # MLflow dependencies
└── create_bucket.py           # MinIO bucket initialization
```

## Quick Start

### 1. Start MLflow Stack

```bash
cd docker
docker-compose -f docker-compose.mlflow.yml up -d
```

This starts:
- **MLflow Tracking Server**: http://localhost:5000
- **MinIO Console**: http://localhost:9001 (admin/minio_admin_password)
- **Postgres**: localhost:5433 (for MLflow tracking database)

### 2. Generate Test Dataset

```bash
cd backend
python -m evaluations.workout_phase_dataset
```

This creates `evaluations/datasets/workout_phase_generation_v1.json` with 10 test cases.

### 3. Run Evaluation

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=your_key_here

# Run the evaluation
python -m evaluations.harness
```

### 4. View Results

Open http://localhost:5000 in your browser to see:
- Experiment runs
- Metrics (overall score, latency, cost, tool accuracy)
- Individual judge scores (output quality, tool selection, response quality, safety)
- Artifacts (agent outputs, judge reasoning, detailed metrics)

## Evaluation Metrics

### LLM-as-a-Judge Metrics (Weighted)

1. **Output Quality (30%)**: Appropriateness of workout design for fitness level, goals, and constraints
2. **Tool Selection (20%)**: Correctness of tool calls and parameters
3. **Response Quality (30%)**: Clarity, helpfulness, and tone of agent responses
4. **Safety (20%)**: Injury risk considerations and appropriate progression

### Custom Metrics

1. **Latency**: Execution time in milliseconds
2. **Cost**: OpenAI API cost in USD (based on token usage)
3. **Tool Usage Accuracy**: Percentage of correct tool calls

## Test Dataset: Workout Phase Agent

10 test cases covering:
- **Beginner scenarios**: Foundation phases, limited equipment, time constraints
- **Intermediate scenarios**: Strength building, fat loss, injury modifications
- **Advanced scenarios**: Hypertrophy focus, strength peaking, high frequency training
- **Special populations**: Seniors, bodyweight-only, home workouts

Each test case includes:
- User profile (fitness level, equipment, injuries)
- Phase requirements (objectives, duration)
- Workout preferences (frequency, duration, schedule)
- Expected output validation criteria
- Evaluation criteria for judges

## Adding New Agent Evaluations

### 1. Create Test Dataset

```python
from evaluations.dataset_schema import TestCase, EvaluationDataset

# Define test cases for your agent
test_cases = [
    TestCase(
        id="my_agent_001",
        description="Test case description",
        input={"key": "value"},
        expected_output={"expected": "output"},
        evaluation_criteria={
            "output_quality": {"weight": 0.3, "aspects": [...]},
            # ... other criteria
        }
    ),
    # ... more test cases
]

# Create dataset
dataset = EvaluationDataset(
    name="my_agent_eval_v1",
    version="1.0.0",
    description="Evaluation for my agent",
    agent_name="my_agent",
    test_cases=test_cases
)
```

### 2. Create Agent Runner

```python
async def my_agent_runner(
    input_data: dict[str, Any],
    collector: MetricsCollector
) -> dict[str, Any]:
    """Run your agent and collect metrics."""
    
    # Run agent
    result = await my_agent.run(input_data)
    
    # Record LLM calls
    collector.record_llm_call(
        model="gpt-4o",
        input_text=prompt,
        output_text=response
    )
    
    # Record tool calls
    collector.record_tool_call(
        tool_name="my_tool",
        parameters=params,
        is_correct=True
    )
    
    return result
```

### 3. Run Evaluation

```python
from evaluations.harness import EvaluationHarness

harness = EvaluationHarness(
    agent_runner=my_agent_runner,
    experiment_name="my_agent_eval",
    mlflow_tracking_uri="http://localhost:5000"
)

results = await harness.run_evaluation(
    dataset=my_dataset,
    run_name="baseline"
)
```

## Configuration

### Environment Variables

```bash
# OpenAI API key (required for LLM judges)
export OPENAI_API_KEY=your_key_here

# MLflow tracking URI (optional, defaults to http://localhost:5000)
export MLFLOW_TRACKING_URI=http://localhost:5000
```

### MLflow Stack Configuration

Edit `docker/docker-compose.mlflow.yml` to change:
- Postgres credentials
- MinIO credentials
- Port mappings
- Resource limits

## Troubleshooting

### MLflow UI not loading

```bash
# Check if services are running
docker-compose -f docker/docker-compose.mlflow.yml ps

# Check logs
docker-compose -f docker/docker-compose.mlflow.yml logs mlflow-server
```

### MinIO bucket creation failed

```bash
# Manually create bucket
docker exec -it mlflow-minio mc alias set minio http://localhost:9000 minio_admin minio_admin_password
docker exec -it mlflow-minio mc mb minio/mlflow-artifacts
```

### Evaluation crashes during judge execution

- Check OpenAI API key is set: `echo $OPENAI_API_KEY`
- Check API rate limits (may need to add delays between judge calls)
- Check judge prompt length (may exceed context window)

## Next Steps

1. **Integrate Real Agent**: Replace mock agent runner with actual workout phase agent
2. **Add More Test Cases**: Expand dataset to cover edge cases
3. **Evaluate Other Agents**: Apply pattern to intake, meal, fitness coach, and query agents
4. **Set Up CI/CD**: Run evaluations automatically on code changes
5. **Benchmark Models**: Compare GPT-4o vs GPT-4o-mini vs other models
6. **Optimize Costs**: Identify opportunities to reduce token usage

## Resources

- [MLflow Documentation](https://mlflow.org/docs/latest/)
- [MLflow GenAI Guide](https://mlflow.org/docs/latest/genai/)
- [LLM-as-a-Judge Guide](https://mlflow.org/docs/latest/llms/llm-evaluate/)
- [MLflow Model Serving](https://mlflow.org/docs/latest/models.html)
