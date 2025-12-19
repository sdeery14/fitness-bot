"""Check what datasets exist in MLflow."""
import mlflow
from mlflow.genai.datasets import get_dataset

# List all datasets first
client = mlflow.MlflowClient()
datasets = client.search_datasets()
print(f"Total datasets: {len(datasets)}")
for ds in datasets:
    print(f"  Dataset ID: {ds.dataset_id}")
    print(f"  Name: {ds.name}")
    print(f"  Tags: {ds.tags}")
    print(f"  Has records: {ds.has_records}")
    
    # Get records count
    records = ds.records
    print(f"  Number of records: {len(records)}")

print("\n" + "="*60 + "\n")

# Get the dataset
try:
    dataset = datasets[0] if datasets else None
    if not dataset:
        print("No dataset found!")
        exit(1)
    
    # Convert to list to count
    records = list(dataset)
    
    print(f"Dataset name: {dataset.name}")
    print(f"Number of records: {len(records)}")
    print(f"\nRecord IDs:")
    for i, record in enumerate(records, 1):
        inputs = record.get('inputs', {})
        phase_name = inputs.get('phase_name', 'Unknown')
        diet = inputs.get('dietary_restrictions', [])
        diet_str = ', '.join(diet) if diet else 'omnivore'
        print(f"  {i}. {phase_name} - {diet_str}")
        
except Exception as e:
    print(f"Error: {e}")
