"""Load evaluation datasets into MLflow.

This script uploads test datasets from datasets_simple/ to the MLflow server
running at http://localhost:5000.

Usage:
    # Load all datasets
    uv run python evaluations/load_datasets.py --all
    
    # Load specific dataset
    uv run python evaluations/load_datasets.py --agent workout_phase_agent
    
    # Load with custom MLflow URI
    uv run python evaluations/load_datasets.py --all --mlflow-uri http://localhost:5001

Dataset → Experiment Mapping:
    - workout_phase_simple_v1.json → workout_phase_agent_evaluation (exp_id: 2)
    - intake_simple_v1.json → intake_agent_evaluation (exp_id: 3)
    - fitness_coach_simple_v1.json → fitness_coach_agent_evaluation (exp_id: 4)
    - meal_phase_simple_v1.json → meal_phase_agent_evaluation (exp_id: 5)
    - query_agent_simple_v1.json → query_agent_evaluation (exp_id: 6)
"""

import argparse
import json
import sys
from pathlib import Path

import mlflow
from mlflow.genai.datasets import create_dataset


# Agent → Dataset mapping
AGENT_DATASET_MAP = {
    "workout_phase_agent": {
        "file": "workout_phase_simple_v1.json",
        "experiment_name": "workout_phase_agent_evaluation",
        "experiment_id": 2
    },
    "intake_agent": {
        "file": "intake_simple_v1.json",
        "experiment_name": "intake_agent_evaluation",
        "experiment_id": 3
    },
    "fitness_coach_agent": {
        "file": "fitness_coach_simple_v1.json",
        "experiment_name": "fitness_coach_agent_evaluation",
        "experiment_id": 4
    },
    "meal_phase_agent": {
        "file": "meal_phase_simple_v1.json",
        "experiment_name": "meal_phase_agent_evaluation",
        "experiment_id": 5
    },
    "query_agent": {
        "file": "query_agent_simple_v1.json",
        "experiment_name": "query_agent_evaluation",
        "experiment_id": 6
    }
}


def load_dataset(agent_name: str, mlflow_uri: str = "http://localhost:5000") -> str:
    """Load a dataset into MLflow for a specific agent.
    
    Args:
        agent_name: Name of the agent (e.g., 'workout_phase_agent')
        mlflow_uri: MLflow tracking server URI
        
    Returns:
        str: Dataset ID from MLflow
    """
    if agent_name not in AGENT_DATASET_MAP:
        raise ValueError(f"Unknown agent: {agent_name}. Valid: {list(AGENT_DATASET_MAP.keys())}")
    
    config = AGENT_DATASET_MAP[agent_name]
    
    # Set MLflow tracking URI
    mlflow.set_tracking_uri(mlflow_uri)
    print(f"\n{'='*80}")
    print(f"Loading Dataset: {agent_name}")
    print(f"{'='*80}")
    print(f"MLflow URI: {mlflow_uri}")
    
    # Load dataset from JSON
    dataset_path = Path(__file__).parent / "datasets_simple" / config["file"]
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset_data = json.load(f)
    
    print(f"[OK] Loaded: {dataset_data['name']} v{dataset_data['version']}")
    print(f"     File: {config['file']}")
    print(f"     Test cases: {len(dataset_data['test_cases'])}")
    
    # Get or create experiment
    experiment_name = config["experiment_name"]
    experiment = mlflow.get_experiment_by_name(experiment_name)
    
    if experiment is None:
        experiment_id = mlflow.create_experiment(experiment_name)
        experiment = mlflow.get_experiment(experiment_id)
        print(f"\n[OK] Created experiment: {experiment_name} (ID: {experiment_id})")
    else:
        print(f"\n[OK] Using experiment: {experiment_name} (ID: {experiment.experiment_id})")
    
    # Transform test cases to MLflow format
    mlflow_records = []
    for test_case in dataset_data['test_cases']:
        record = {
            "inputs": test_case["inputs"],
            "expectations": test_case["expectations"],
            "source": test_case.get("source", {"source_type": "HUMAN"}),
            "tags": {
                **test_case.get("tags", {}),
                "test_case_id": test_case["id"]
            }
        }
        mlflow_records.append(record)
    
    # Create dataset in MLflow
    print(f"\nCreating MLflow dataset...")
    dataset = create_dataset(
        name=dataset_data["name"],
        experiment_id=experiment.experiment_id,
        tags={
            "version": dataset_data["version"],
            "description": dataset_data["description"],
            "agent": agent_name
        }
    )
    
    # Merge records
    dataset.merge_records(mlflow_records)
    
    print(f"[OK] Dataset created!")
    print(f"     Dataset ID: {dataset.dataset_id}")
    print(f"     Records: {len(mlflow_records)}")
    print(f"\nTest Cases:")
    for i, test_case in enumerate(dataset_data['test_cases'], 1):
        print(f"  {i}. {test_case['id']}: {test_case.get('inputs', {}).get('phase_name', test_case.get('inputs', {}).get('messages', [{}])[0].get('content', 'N/A')[:60])}")
    
    return dataset.dataset_id


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Load evaluation datasets into MLflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load all datasets
  uv run python evaluations/load_datasets.py --all
  
  # Load specific dataset
  uv run python evaluations/load_datasets.py --agent meal_phase_agent
  
  # Use different MLflow server
  uv run python evaluations/load_datasets.py --all --mlflow-uri http://localhost:5001
        """
    )
    parser.add_argument(
        "--agent",
        type=str,
        choices=list(AGENT_DATASET_MAP.keys()),
        help="Agent to load dataset for"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Load datasets for all agents"
    )
    parser.add_argument(
        "--mlflow-uri",
        type=str,
        default="http://localhost:5000",
        help="MLflow tracking server URI (default: http://localhost:5000)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.all and not args.agent:
        parser.error("Must specify either --agent or --all")
    
    # Load datasets
    dataset_ids = {}
    
    if args.all:
        print("\n" + "="*80)
        print("Loading ALL Datasets")
        print("="*80)
        
        for agent_name in AGENT_DATASET_MAP.keys():
            try:
                dataset_id = load_dataset(agent_name, args.mlflow_uri)
                dataset_ids[agent_name] = dataset_id
            except Exception as e:
                print(f"\n[ERROR] Failed to load {agent_name}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Print summary
        print("\n" + "="*80)
        print("Summary: All Datasets Loaded")
        print("="*80)
        for agent_name, dataset_id in dataset_ids.items():
            print(f"  {agent_name}: {dataset_id}")
        
        print(f"\nNext step: Run evaluations")
        print(f"  uv run python evaluations/run_evaluation.py --agent all --run-name 'baseline_v1'")
    else:
        dataset_id = load_dataset(args.agent, args.mlflow_uri)
        dataset_ids[args.agent] = dataset_id
        
        print(f"\nNext step: Run evaluation")
        print(f"  uv run python evaluations/run_evaluation.py --agent {args.agent} --run-name 'your_run_name'")
    
    return dataset_ids


if __name__ == "__main__":
    main()
