"""Upload simple evaluation datasets to MLflow."""

import json
import mlflow
from pathlib import Path
from mlflow.genai.datasets import create_dataset


def upload_simple_dataset(dataset_name: str, agent_name: str):
    """Upload a simple evaluation dataset to MLflow.
    
    Args:
        dataset_name: Name of the JSON file (without extension)
        agent_name: Name of the agent (for tags and experiment)
    """
    mlflow.set_tracking_uri("http://localhost:5000")
    
    # Load dataset
    dataset_path = Path(__file__).parent / "datasets_simple" / f"{dataset_name}.json"
    print(f"\nLoading dataset: {dataset_path.name}")
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset_data = json.load(f)
    
    print(f"[OK] Loaded: {dataset_data['name']} v{dataset_data['version']}")
    print(f"  Description: {dataset_data['description']}")
    print(f"  Test cases: {len(dataset_data['test_cases'])}")
    
    # Set or create experiment
    experiment_name = f"{agent_name}_evaluation"
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
    print(f"\nCreating MLflow Evaluation Dataset...")
    dataset = create_dataset(
        name=dataset_data["name"],
        experiment_id=experiment.experiment_id,
        tags={
            "version": dataset_data["version"],
            "agent": agent_name,
            "description": dataset_data["description"],
            "test_count": str(len(mlflow_records)),
        }
    )
    
    print(f"[OK] Created dataset with ID: {dataset.dataset_id}")
    
    # Add records using merge_records (MLflow 3.7.0 API)
    print(f"\nAdding {len(mlflow_records)} records to dataset...")
    dataset.merge_records(mlflow_records)
    print(f"  [OK] Added {len(mlflow_records)} records")
    
    print(f"\n{'='*80}")
    print(f"[SUCCESS] Dataset uploaded to MLflow!")
    print(f"{'='*80}")
    print(f"  Dataset ID: {dataset.dataset_id}")
    print(f"  Records: {len(mlflow_records)}")
    print(f"  View at: http://localhost:5000/#/experiments/{experiment.experiment_id}/evaluation-datasets")
    print(f"{'='*80}")
    
    return dataset


def main():
    """Upload all simple datasets."""
    print("="*80)
    print("Uploading Simple Evaluation Datasets to MLflow")
    print("="*80)
    
    datasets_to_upload = [
        ("workout_phase_simple_v1", "workout_phase_agent"),
        ("intake_simple_v1", "intake_agent"),
        ("fitness_coach_simple_v1", "fitness_coach_agent"),
    ]
    
    uploaded_datasets = []
    
    for dataset_name, agent_name in datasets_to_upload:
        try:
            dataset = upload_simple_dataset(dataset_name, agent_name)
            uploaded_datasets.append((dataset_name, dataset.dataset_id))
            print()  # Blank line between uploads
        except Exception as e:
            print(f"\n[ERROR] Failed uploading {dataset_name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Summary
    print("\n" + "="*80)
    print("Upload Summary")
    print("="*80)
    for name, dataset_id in uploaded_datasets:
        print(f"  [OK] {name}: {dataset_id}")
    print(f"\nTotal: {len(uploaded_datasets)} datasets uploaded")
    print("="*80)


if __name__ == "__main__":
    main()
