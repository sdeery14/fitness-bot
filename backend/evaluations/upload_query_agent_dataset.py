"""Upload query_agent evaluation dataset to MLflow."""

import json
import mlflow
from pathlib import Path
from mlflow.genai.datasets import create_dataset


def upload_query_agent_dataset():
    """Upload query agent evaluation dataset to MLflow."""

    # Set tracking URI
    mlflow.set_tracking_uri("http://localhost:5000")

    # Create or get experiment
    experiment_name = "query_agent_eval"
    experiment = mlflow.set_experiment(experiment_name)
    print(f"✓ Using experiment: {experiment_name} (ID: {experiment.experiment_id})")

    # Load our JSON dataset
    dataset_path = Path(__file__).parent / "datasets_simple" / "query_agent_simple_v1.json"
    with open(dataset_path, "r") as f:
        dataset_data = json.load(f)

    print(f"✓ Loaded dataset: {dataset_data['name']} v{dataset_data['version']}")
    print(f"  Test cases: {len(dataset_data['test_cases'])}")

    # Transform to MLflow format
    mlflow_records = []

    for test_case in dataset_data["test_cases"]:
        record = {
            "inputs": test_case["inputs"],
            "expectations": test_case["expectations"],
            "source": test_case.get("source", {}),
            "tags": test_case.get("tags", {}),
        }
        mlflow_records.append(record)

    # Create MLflow Evaluation Dataset
    print(f"\nCreating MLflow Evaluation Dataset...")

    dataset = create_dataset(
        name=dataset_data["name"],
        experiment_id=experiment.experiment_id,
        tags={
            "version": dataset_data["version"],
            "agent": "query_agent",
            "description": dataset_data["description"],
            "test_count": str(len(mlflow_records)),
            "mlflow_version": "3.7.0",
        },
    )

    print(f"✓ Created dataset with ID: {dataset.dataset_id}")

    # Add records to the dataset
    print(f"\nAdding {len(mlflow_records)} records to dataset...")
    dataset.merge_records(mlflow_records)
    print(f"  ✓ Added {len(mlflow_records)} records")

    print(f"\n✓ Successfully uploaded dataset to MLflow!")
    print(f"  Dataset ID: {dataset.dataset_id}")
    print(f"  Records: {len(mlflow_records)}")
    print(
        f"  View at: http://localhost:5000/#/experiments/{experiment.experiment_id}/evaluation-datasets"
    )

    return dataset


if __name__ == "__main__":
    print("=" * 80)
    print("Uploading Query Agent Evaluation Dataset to MLflow")
    print("=" * 80)

    try:
        dataset = upload_query_agent_dataset()
        print("\n" + "=" * 80)
        print("✓ Upload Complete!")
        print("=" * 80)
        print(f"\nDataset ID: {dataset.dataset_id}")
        print("\nAdd this to run_evaluation.py agent_configs:")
        print(f'"query_agent": {{')
        print(f'    "experiment_id": 6,  # query_agent_eval')
        print(f'    "dataset_id": "{dataset.dataset_id}",')
        print(f'}},')
    except Exception as e:
        print(f"\n✗ Error uploading dataset: {e}")
        import traceback

        traceback.print_exc()
