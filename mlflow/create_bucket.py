"""Create MinIO bucket for MLflow artifacts if it doesn't exist."""
import time
import boto3
from botocore.exceptions import ClientError

def create_bucket():
    """Create the mlflow-artifacts bucket in MinIO."""
    # Wait for MinIO to be ready
    time.sleep(5)
    
    s3_client = boto3.client(
        's3',
        endpoint_url='http://mlflow-minio:9000',
        aws_access_key_id='minio_admin',
        aws_secret_access_key='minio_admin_password',
    )
    
    bucket_name = 'mlflow-artifacts'
    
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✓ Bucket '{bucket_name}' already exists")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            # Bucket doesn't exist, create it
            s3_client.create_bucket(Bucket=bucket_name)
            print(f"✓ Created bucket '{bucket_name}'")
        else:
            print(f"✗ Error checking bucket: {e}")
            raise

if __name__ == '__main__':
    create_bucket()
