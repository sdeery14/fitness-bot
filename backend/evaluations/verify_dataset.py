"""Verify dataset uploaded to MLflow."""

import mlflow
from mlflow.genai.datasets import search_datasets, get_dataset


def verify_dataset():
    """Verify the dataset was uploaded correctly."""
    mlflow.set_tracking_uri("http://localhost:5000")
    
    print("Searching for datasets...")
    datasets = search_datasets(
        filter_string="name LIKE '%workout_phase%'",
        order_by=["last_update_time DESC"]
    )
    
    print(f"\nFound {len(datasets)} dataset(s):")
    for ds in datasets:
        print(f"  - {ds.name} (ID: {ds.dataset_id})")
        print(f"    Tags: {ds.tags}")
        print(f"    Records: {len(ds.records) if hasattr(ds, 'records') else 'Unknown'}")
    
    # Get the latest dataset
    if datasets:
        dataset = datasets[0]
        print(f"\n{'='*80}")
        print(f"Dataset Details: {dataset.name}")
        print(f"{'='*80}")
        print(f"ID: {dataset.dataset_id}")
        print(f"Experiment IDs: {dataset.experiment_ids}")
        print(f"Tags: {dataset.tags}")
        print(f"Created by: {dataset.created_by}")
        print(f"Last updated by: {dataset.last_updated_by}")
        
        # Check if has_records (property that exists based on error message)
        print(f"\nHas records: {dataset.has_records if hasattr(dataset, 'has_records') else 'Unknown'}")
        
        # Try to get records via to_df() or other method
        try:
            df = dataset.to_df()
            print(f"\n{'='*80}")
            print(f"Dataset Records (via DataFrame)")
            print(f"{'='*80}")
            print(f"Shape: {df.shape}")
            print(f"\nColumns: {list(df.columns)}")
            print(f"\nFirst few rows:")
            print(df.head())
        except Exception as e:
            print(f"\n✗ Could not convert to DataFrame: {e}")
        
        # Show dataset attributes
        print(f"\n{'='*80}")
        print(f"Dataset Attributes")
        print(f"{'='*80}")
        attrs = [attr for attr in dir(dataset) if not attr.startswith('_')]
        for attr in attrs:
            try:
                value = getattr(dataset, attr)
                if not callable(value):
                    print(f"  {attr}: {value}")
            except:
                pass
        
        return dataset
    
    return None


if __name__ == "__main__":
    verify_dataset()
