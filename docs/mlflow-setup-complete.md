# MLflow Evaluation Setup Complete ✅

## What We Built

### 1. **MLflow Infrastructure** (Docker Stack)
   - **MLflow Tracking Server**: Experiment tracking and metrics logging
   - **PostgreSQL**: Persistent tracking database
   - **MinIO**: S3-compatible artifact storage
   - **Ports**: MLflow UI (5000), MinIO Console (9001), Postgres (5433)

### 2. **Evaluation Framework** (Python)
   ```
   backend/evaluations/
   ├── dataset_schema.py          # Pydantic schemas for test cases
   ├── workout_phase_dataset.py   # 10 test cases for workout agent
   ├── llm_judges.py              # 4 LLM-as-a-judge evaluators
   ├── custom_metrics.py          # Latency, cost, tool usage metrics
   ├── harness.py                 # Main evaluation runner
   ├── setup.py                   # Automated setup script
   ├── README.md                  # Complete documentation
   └── datasets/
       └── workout_phase_generation_v1.json  # Generated test cases
   ```

### 3. **Test Dataset** (10 Cases)
   - **Beginner**: Foundation phases, limited equipment, time constraints
   - **Intermediate**: Strength building, fat loss, injury modifications
   - **Advanced**: Hypertrophy focus, strength peaking, high frequency
   - **Special**: Seniors, bodyweight-only, home workouts

### 4. **Evaluation Metrics**

   **LLM-as-a-Judge (Weighted):**
   - Output Quality (30%): Workout appropriateness for level/goals
   - Tool Selection (20%): Correct tool calls and parameters
   - Response Quality (30%): Clarity, helpfulness, coaching tone
   - Safety (20%): Injury risk and progression appropriateness

   **Custom Metrics:**
   - Latency: Execution time in milliseconds
   - Cost: OpenAI API cost in USD
   - Tool Usage Accuracy: % of correct tool calls

## Quick Start

### 1. Start MLflow Stack
```bash
cd docker
docker-compose -f docker-compose.mlflow.yml up -d
```

View at: http://localhost:5000

### 2. Run Evaluation (Mock)
```bash
cd backend
export OPENAI_API_KEY=your_key_here
python -m evaluations.harness
```

This runs the mock agent runner against all 10 test cases.

### 3. View Results
Open http://localhost:5000 to see:
- Experiment runs with metrics
- Individual judge scores and reasoning
- Artifacts (agent outputs, metrics JSON)

## Next Steps

### Immediate (Ready to Implement)
1. **Integrate Real Workout Phase Agent**
   - Replace `mock_agent_runner` in harness.py
   - Connect to actual workout generation logic
   - Test with first evaluation run

2. **Run Baseline Evaluation**
   - Execute full evaluation suite
   - Establish baseline metrics
   - Identify improvement areas

### Short-Term (Week 1-2)
3. **Add More Test Cases**
   - Edge cases (very short plans, unusual goals)
   - Error scenarios (missing data, invalid inputs)
   - Expand to 20-30 test cases

4. **Evaluate Other Agents**
   - Intake Agent: 15 test cases for onboarding flow
   - Meal Phase Agent: 10 test cases for nutrition planning
   - Fitness Coach Agent: 20 test cases for query/update/build
   - Query Agent: 15 test cases for plan queries

### Medium-Term (Week 3-4)
5. **Optimize Performance**
   - Identify high-cost operations
   - Reduce latency bottlenecks
   - Optimize token usage

6. **Model Comparison**
   - Benchmark GPT-4o vs GPT-4o-mini
   - Cost-performance trade-offs
   - Select optimal model per agent

### Long-Term (Month 2+)
7. **Automated Test Generation**
   - Build AI agent that generates test cases
   - Conversational interface for dataset creation
   - Continuous expansion of test coverage

8. **CI/CD Integration**
   - Run evaluations on every commit
   - Block merges if scores drop
   - Track metrics over time

9. **MLflow Model Serving** (Optional)
   - Wrap agents as MLflow models
   - Deploy through MLflow serving
   - Streamline eval-to-deployment workflow

## Architecture Decisions

✅ **Separate Docker Compose** - Keeps eval infrastructure independent from main app

✅ **LLM-as-a-Judge** - Scalable quality assessment without manual labeling

✅ **Custom Metrics** - Track latency and cost alongside quality

✅ **Modular Design** - Easy to extend to other agents (reusable components)

✅ **Mock Runner** - Can test framework without running actual agents

✅ **Version Control** - Datasets, schemas, and evaluators in git

## File Structure Summary

```
docker/
└── docker-compose.mlflow.yml       # MLflow stack definition

mlflow/
├── Dockerfile                      # MLflow server image
├── requirements.txt                # MLflow dependencies
└── create_bucket.py                # MinIO initialization

backend/
├── requirements.txt                # Added mlflow, tiktoken, boto3
└── evaluations/
    ├── dataset_schema.py           # Test case schemas
    ├── workout_phase_dataset.py    # 10 test cases
    ├── llm_judges.py               # 4 judge evaluators
    ├── custom_metrics.py           # Latency, cost, tool usage
    ├── harness.py                  # Evaluation runner
    ├── setup.py                    # Setup automation
    ├── README.md                   # Documentation
    ├── requirements.txt            # Eval dependencies
    └── datasets/
        └── workout_phase_generation_v1.json  # Generated dataset
```

## Dependencies Added

**backend/requirements.txt:**
- `mlflow==2.19.0` - Experiment tracking and evaluation
- `tiktoken==0.8.0` - Token counting for cost calculation
- `boto3==1.35.77` - MinIO/S3 artifact storage

**Already Had:**
- `openai>=2.7.1` - LLM-as-a-judge API calls
- `pydantic>=2.12.3` - Dataset schemas

## Key Features

1. **End-to-End Workflow**: Dataset → Agent → Metrics → Logging → UI
2. **Comprehensive Metrics**: Quality scores + performance + cost
3. **Detailed Artifacts**: Every run logs outputs, reasoning, metrics
4. **Extensible Design**: Easy to add agents, test cases, metrics
5. **Production-Ready**: Self-hosted infrastructure, version control

## Commit

```bash
git commit 9d56d38
"Add MLflow evaluation framework for AI agents"
- 14 files changed, 3300 insertions(+)
```

## Next Action

**Choose one:**

A. **Start MLflow and test workflow**
   ```bash
   cd docker
   docker-compose -f docker-compose.mlflow.yml up -d
   # Wait for services to start
   cd ../backend
   python -m evaluations.harness  # Run mock evaluation
   ```

B. **Integrate real workout phase agent**
   - Update harness.py agent_runner
   - Connect to actual workout generation
   - Run first real evaluation

C. **Add evaluation for another agent** (e.g., Intake Agent)
   - Create intake_agent_dataset.py
   - Define 10-15 test cases
   - Run evaluation

**Recommendation**: Start with A to verify the stack works, then proceed to B for real data.
