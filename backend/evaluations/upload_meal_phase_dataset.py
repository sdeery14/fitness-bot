"""
Upload meal_phase_simple_v1 dataset to MLflow.
Creates experiment 5 if needed and uploads the dataset.
"""
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import mlflow
from mlflow.genai.datasets import create_dataset

# Load environment from backend/.env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(TRACKING_URI)

def upload_meal_phase_dataset():
    """Upload meal_phase_simple_v1 dataset to experiment 5."""
    
    # Read the dataset file
    dataset_path = Path(__file__).parent / "datasets_simple" / "meal_phase_simple_v1.json"
    
    if not dataset_path.exists():
        print(f"❌ Dataset file not found: {dataset_path}")
        print("Run create_mlflow_datasets.py first to generate the file")
        return None
    
    with open(dataset_path) as f:
        dataset_data = json.load(f)
    
    print(f"[OK] Loaded: {dataset_data['name']} v{dataset_data['version']}")
    print(f"  Description: {dataset_data['description']}")
    print(f"  Test cases: {len(dataset_data['test_cases'])}")
    
    # Create or get experiment 5
    experiment_name = "meal_phase_agent_evaluation"
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(experiment_name)
            experiment = mlflow.get_experiment(experiment_id)
            print(f"\n[OK] Created experiment: {experiment_name} (ID: {experiment_id})")
        else:
            print(f"\n[OK] Using experiment: {experiment_name} (ID: {experiment.experiment_id})")
    except Exception as e:
        print(f"❌ Error creating experiment: {e}")
        return None
    
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
    
    # Create dataset in MLflow using genai.datasets API
    print(f"\nCreating MLflow Evaluation Dataset...")
    try:
        dataset = create_dataset(
            name=dataset_data["name"],
            experiment_id=experiment.experiment_id,
            tags={
                "version": dataset_data["version"],
                "agent": "meal_phase_agent",
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
        
        return dataset.dataset_id
            
    except Exception as e:
        print(f"❌ Error uploading dataset: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("="*80)
    print("Uploading meal_phase_simple_v1 Dataset to MLflow")
    print("="*80)
    print(f"MLflow URI: {TRACKING_URI}\n")
    
    dataset_id = upload_meal_phase_dataset()
    
    if dataset_id:
        print("\n" + "="*80)
        print("Next Steps:")
        print("="*80)
        print(f"1. Update run_evaluation.py with dataset_id: {dataset_id}")
        print(f"2. Run: uv run python evaluations/run_evaluation.py --agent meal_phase_agent")
