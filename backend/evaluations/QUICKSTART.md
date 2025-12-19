# Evaluation Quick Start Guide

**Complete workflow for running agent evaluations with MLflow.**

## Prerequisites

1. **MLflow server must be running**
   ```bash
   cd backend
   uv run mlflow ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns --port 5000
   ```
   
   Verify: http://localhost:5000 should show MLflow UI

## Step-by-Step Workflow

### 1️⃣ Load Datasets

Upload test datasets from `datasets_simple/` to MLflow server:

```bash
# Load all datasets (first time setup)
uv run python evaluations/load_datasets.py --all

# Or load specific dataset
uv run python evaluations/load_datasets.py --agent meal_phase_agent
```

**What this does:**
- Reads JSON files from `datasets_simple/`
- Creates/verifies experiments in MLflow
- Uploads test cases to MLflow
- Prints dataset IDs (automatically used by run_evaluation.py)

**Expected output:**
```
================================================================================
Loading Dataset: meal_phase_agent
================================================================================
MLflow URI: http://localhost:5000
[OK] Loaded: meal_phase_simple_v1 v1.0.0
     File: meal_phase_simple_v1.json
     Test cases: 2

[OK] Using experiment: meal_phase_agent_evaluation (ID: 5)

Creating MLflow dataset...
[OK] Dataset created!
     Dataset ID: d-09627bd84c704c1b88f227bd1f3eb2f5
     Records: 2
```

### 2️⃣ Run Evaluation

Execute agent tests with LLM judges:

```bash
# Run all agents
uv run python evaluations/run_evaluation.py --agent all --run-name "baseline_v1"

# Or run specific agent
uv run python evaluations/run_evaluation.py --agent meal_phase_agent --run-name "iteration_v2"
```

**What this does:**
- Loads dataset from MLflow using configured dataset ID
- Executes agent with each test case
- Evaluates outputs with LLM judges
- Stores results as traces in MLflow

**Expected output:**
```
================================================================================
Running Evaluation: meal_phase_agent
================================================================================
Dataset ID: d-09627bd84c704c1b88f227bd1f3eb2f5
Experiment ID: 5
MLflow URI: http://localhost:5000

[OK] Loaded dataset: meal_phase_simple_v1
[OK] Agent runner: run_meal_phase_agent
[OK] Judges: ['meal_phase_quality', 'safety_compliance']

Running evaluation...
This will:
  1. Execute agent on test cases
  2. Evaluate outputs with 2 LLM judge(s)
  3. Track results in MLflow

================================================================================
Evaluation Complete!
================================================================================
Results:
  Run Name: iteration_v2
  View at: http://localhost:5000/#/experiments/5
```

### 3️⃣ View Results

**Option A: MLflow Web UI** (Recommended)
1. Open http://localhost:5000
2. Navigate to experiment (e.g., "meal_phase_agent_evaluation")
3. Click on run name (e.g., "iteration_v2")
4. View traces, assessments, and metrics

**Option B: Query Traces with CLI**
```bash
uv run mlflow traces search --experiment-id 5 --max-results 10 --output json
```

**Option C: Generate Report**
Use MLflow MCP server to query and analyze results. See `meal_phase_v2_10tests_report.md` for example.

## Common Scenarios

### Scenario 1: First Time Setup
```bash
# 1. Start MLflow server (separate terminal)
cd backend
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000

# 2. Load all datasets (in another terminal)
uv run python evaluations/load_datasets.py --all

# 3. Run baseline evaluation
uv run python evaluations/run_evaluation.py --agent all --run-name "baseline_v1"
```

### Scenario 2: Iterating on Single Agent
```bash
# 1. Make changes to agent code (e.g., meal_phase_agent.py)

# 2. Re-run evaluation with new run name
uv run python evaluations/run_evaluation.py --agent meal_phase_agent --run-name "fix_percentage_math"

# 3. Compare results in MLflow UI
# Navigate to experiment 5, compare traces from different runs
```

### Scenario 3: Updating Test Dataset
```bash
# 1. Edit JSON file in datasets_simple/
#    Example: datasets_simple/meal_phase_simple_v1.json

# 2. Reload dataset to MLflow
uv run python evaluations/load_datasets.py --agent meal_phase_agent

# 3. Run evaluation with new dataset
uv run python evaluations/run_evaluation.py --agent meal_phase_agent --run-name "new_test_cases"
```

## Agent → Experiment Mapping

| Agent Name | Experiment ID | Dataset File |
|------------|---------------|--------------|
| workout_phase_agent | 2 | workout_phase_simple_v1.json |
| intake_agent | 3 | intake_simple_v1.json |
| fitness_coach_agent | 4 | fitness_coach_simple_v1.json |
| meal_phase_agent | 5 | meal_phase_simple_v1.json |
| query_agent | 6 | query_agent_simple_v1.json |

## Troubleshooting

### "Connection refused" error
**Problem**: MLflow server not running  
**Solution**: Start MLflow server:
```bash
cd backend
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

### "Dataset not found" error
**Problem**: Dataset not loaded into MLflow  
**Solution**: Load dataset:
```bash
uv run python evaluations/load_datasets.py --agent meal_phase_agent
```

### Wrong MLflow server URL
**Problem**: Using local SQLite instead of http://localhost:5000  
**Solution**: Both scripts default to http://localhost:5000. If using different port:
```bash
uv run python evaluations/load_datasets.py --agent meal_phase_agent --mlflow-uri http://localhost:5001
```

## Next Steps

1. ✅ Review evaluation results in MLflow UI
2. 📊 Generate comprehensive report (see meal_phase_v2_10tests_report.md)
3. 🔧 Implement fixes based on findings
4. 🔄 Re-run evaluation with new run name
5. 📈 Compare before/after metrics

---

**See also:**
- [README.md](README.md) - Full documentation
- [DATASET_DESIGN.md](DATASET_DESIGN.md) - Dataset schema guide
- [meal_phase_v2_10tests_report.md](meal_phase_v2_10tests_report.md) - Example evaluation report
