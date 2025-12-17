"""Upload evaluation dataset to MLflow as an Evaluation Dataset.

MLflow 3.7.0 introduced Evaluation Datasets - a structured way to manage
test data with inputs, expectations, and metadata for systematic evaluation.

This script transforms our JSON dataset into MLflow's evaluation dataset format.
"""
import json
import mlflow
from pathlib import Path
from mlflow.genai.datasets import create_dataset


def upload_workout_phase_dataset():
    """Upload workout phase evaluation dataset to MLflow."""
    
    # Set tracking URI
    mlflow.set_tracking_uri("http://localhost:5000")
    
    # Create or get experiment
    experiment_name = "workout_phase_agent_eval"
    experiment = mlflow.set_experiment(experiment_name)
    print(f"✓ Using experiment: {experiment_name} (ID: {experiment.experiment_id})")
    
    # Load our JSON dataset
    dataset_path = Path(__file__).parent / "datasets" / "workout_phase_generation_v1.json"
    with open(dataset_path, "r") as f:
        dataset_data = json.load(f)
    
    print(f"✓ Loaded dataset: {dataset_data['name']} v{dataset_data['version']}")
    print(f"  Test cases: {len(dataset_data['data'])}")
    
    # Transform to MLflow format
    # MLflow expects: inputs (dict), expectations (dict), and optional metadata
    mlflow_records = []
    
    for test_case in dataset_data['data']:
        record = {
            "inputs": test_case["input"],  # User profile, phase requirements
            "expectations": test_case["expected_output"],  # Expected workout characteristics
            "metadata": {
                "test_case_id": test_case["id"],
                "description": test_case["description"],
                "evaluation_criteria": test_case.get("evaluation_criteria", {}),
                **test_case.get("metadata", {})
            }
        }
        mlflow_records.append(record)
    
    # Create MLflow Evaluation Dataset
    print(f"\nCreating MLflow Evaluation Dataset...")
    
    dataset = create_dataset(
        name="workout_phase_generation_v1",
        experiment_id=experiment.experiment_id,
        tags={
            "version": dataset_data["version"],
            "agent": "workout_phase_agent",
            "description": dataset_data["description"],
            "test_count": str(len(mlflow_records)),
            "categories": "beginner,intermediate,advanced,injury,time-constrained,bodyweight",
        }
    )
    
    print(f"✓ Created dataset with ID: {dataset.dataset_id}")
    
    # Add records to the dataset using merge_records (MLflow 3.7.0 API)
    print(f"\nAdding {len(mlflow_records)} records to dataset...")
    dataset.merge_records(mlflow_records)
    print(f"  ✓ Added {len(mlflow_records)} records")
    
    print(f"\n✓ Successfully uploaded dataset to MLflow!")
    print(f"  Dataset ID: {dataset.dataset_id}")
    print(f"  Records: {len(mlflow_records)}")
    print(f"  View at: http://localhost:5000/#/experiments/{experiment.experiment_id}/evaluation-datasets")
    
    return dataset


def main():
    """Main entry point."""
    print("="*80)
    print("Uploading Workout Phase Evaluation Dataset to MLflow")
    print("="*80)
    
    try:
        dataset = upload_workout_phase_dataset()
        print("\n" + "="*80)
        print("✓ Upload Complete!")
        print("="*80)
        return dataset
    except Exception as e:
        print(f"\n✗ Error uploading dataset: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
