"""Run MLflow evaluation on fitness agents.

This script:
1. Loads datasets from MLflow by experiment ID
2. Runs agents on test inputs
3. Evaluates outputs using LLM judges
4. Tracks results in MLflow
"""

import argparse
import sys
from pathlib import Path

# Add backend directory to path to enable imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = backend_dir / ".env"
load_dotenv(env_path)

import mlflow
from mlflow.genai import evaluate
from mlflow.genai.datasets import get_dataset

from evaluations.judges import get_judges_for_agent
from evaluations.agent_runners import get_agent_runner


def run_evaluation(
    agent_name: str,
    experiment_id: int,
    dataset_id: str,
    run_name: str | None = None,
):
    """Run evaluation for a specific agent.
    
    Args:
        agent_name: One of 'workout_phase_agent', 'intake_agent', 'fitness_coach_agent'
        experiment_id: MLflow experiment ID to track evaluation run
        dataset_id: MLflow dataset ID (e.g., 'd-e984081e783a491a869dafc6c9e3e403')
        run_name: Optional name for this evaluation run
    """
    # Set MLflow tracking
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment(experiment_id=str(experiment_id))
    
    print(f"=" * 80)
    print(f"Running Evaluation: {agent_name}")
    print(f"=" * 80)
    print(f"Dataset ID: {dataset_id}")
    print(f"Experiment ID: {experiment_id}")
    print(f"MLflow URI: http://localhost:5000")
    print()
    
    # Load dataset from MLflow
    print(f"Loading dataset from MLflow...")
    dataset = get_dataset(dataset_id=dataset_id)
    print(f"[OK] Loaded dataset: {dataset.name}")
    print()
    
    # Get agent runner and judges
    print(f"Preparing evaluation components...")
    agent_runner = get_agent_runner(agent_name)
    judges = get_judges_for_agent(agent_name)
    print(f"[OK] Agent runner: {agent_runner.__name__}")
    print(f"[OK] Judges: {[j.name for j in judges]}")
    print()
    
    # Run evaluation
    print(f"Running evaluation...")
    print(f"This will:")
    print(f"  1. Execute agent on test cases")
    print(f"  2. Evaluate outputs with {len(judges)} LLM judge(s)")
    print(f"  3. Track results in MLflow")
    print()
    
    eval_run_name = run_name or f"{agent_name}_eval"
    
    # Start MLflow run with custom name
    with mlflow.start_run(run_name=eval_run_name):
        results = evaluate(
            data=dataset,
            predict_fn=agent_runner,
            scorers=judges,
        )
    
    print(f"\n{'=' * 80}")
    print(f"Evaluation Complete!")
    print(f"{'=' * 80}")
    print(f"Results:")
    print(f"  Run Name: {eval_run_name}")
    print(f"  View at: http://localhost:5000/#/experiments/{experiment_id}")
    print()
    
    # Print summary metrics
    if hasattr(results, 'metrics'):
        print("Metrics Summary:")
        for metric_name, metric_value in results.metrics.items():
            print(f"  {metric_name}: {metric_value}")
    
    return results


def main():
    """Main entry point for evaluation script."""
    parser = argparse.ArgumentParser(description="Run MLflow evaluation on fitness agents")
    parser.add_argument(
        "--agent",
        type=str,
        required=True,
        choices=["workout_phase_agent", "intake_agent", "fitness_coach_agent", "meal_phase_agent", "query_agent", "all"],
        help="Which agent to evaluate (or 'all' for all agents)"
    )
    parser.add_argument(
        "--run-name",
        type=str,
        default=None,
        help="Optional name for this evaluation run"
    )
    
    args = parser.parse_args()
    
    # Agent-to-experiment mapping with dataset IDs
    # These IDs were returned when we uploaded datasets
    agent_configs = {
        "workout_phase_agent": {
            "experiment_id": 2,
            "dataset_id": "d-e984081e783a491a869dafc6c9e3e403"
        },
        "intake_agent": {
            "experiment_id": 3,
            "dataset_id": "d-716eb2427527401bbe1b957e60a3c39e"
        },
        "fitness_coach_agent": {
            "experiment_id": 4,
            "dataset_id": "d-c97983c9ec99494fbb63ec1bc534c0fe",
        },
        "meal_phase_agent": {
            "experiment_id": 5,
            "dataset_id": "d-e87ebc1a7d654daab83bacc43579ee61",
        },
        "query_agent": {
            "experiment_id": 6,
            "dataset_id": "d-493cf40ba48e49c6bfeb96103ef9336f",
        },
    }
    
    # Run evaluation(s)
    if args.agent == "all":
        print("\n" + "=" * 80)
        print("Running ALL Agent Evaluations")
        print("=" * 80 + "\n")
        
        for agent_name, config in agent_configs.items():
            try:
                run_evaluation(
                    agent_name=agent_name,
                    experiment_id=config["experiment_id"],
                    dataset_id=config["dataset_id"],
                    run_name=args.run_name,
                )
                print("\n")
            except Exception as e:
                print(f"\n[ERROR] Failed to evaluate {agent_name}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print("\n" + "=" * 80)
        print("All Evaluations Complete!")
        print("=" * 80)
    else:
        config = agent_configs[args.agent]
        run_evaluation(
            agent_name=args.agent,
            experiment_id=config["experiment_id"],
            dataset_id=config["dataset_id"],
            run_name=args.run_name,
        )


if __name__ == "__main__":
    main()
