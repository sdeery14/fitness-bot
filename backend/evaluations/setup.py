"""Setup script to initialize MLflow evaluation environment."""
import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
    """Run a shell command and report status."""
    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"{'='*80}")
    print(f"Command: {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print(f"✓ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False


def check_docker():
    """Check if Docker is running."""
    print("\nChecking Docker...")
    try:
        subprocess.run(
            ["docker", "ps"],
            check=True,
            capture_output=True
        )
        print("✓ Docker is running")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Docker is not running or not installed")
        print("  Please install Docker and start Docker Desktop")
        return False


def start_mlflow_stack():
    """Start MLflow stack with docker-compose."""
    docker_dir = Path(__file__).parent.parent.parent / "docker"
    compose_file = docker_dir / "docker-compose.mlflow.yml"
    
    if not compose_file.exists():
        print(f"✗ Compose file not found: {compose_file}")
        return False
    
    cmd = f"docker-compose -f {compose_file} up -d"
    success = run_command(cmd, "Starting MLflow stack")
    
    if success:
        print("\nWaiting for services to be ready...")
        time.sleep(10)
        
        print("\n✓ MLflow stack is running!")
        print(f"  MLflow UI: http://localhost:5000")
        print(f"  MinIO Console: http://localhost:9001")
        print(f"    Username: minio_admin")
        print(f"    Password: minio_admin_password")
    
    return success


def generate_dataset():
    """Generate the workout phase evaluation dataset."""
    script_path = Path(__file__).parent / "workout_phase_dataset.py"
    
    cmd = f"{sys.executable} {script_path}"
    return run_command(cmd, "Generating evaluation dataset")


def check_openai_key():
    """Check if OPENAI_API_KEY is set."""
    import os
    
    print("\nChecking OpenAI API key...")
    if os.getenv("OPENAI_API_KEY"):
        print("✓ OPENAI_API_KEY is set")
        return True
    else:
        print("✗ OPENAI_API_KEY is not set")
        print("  Please set your OpenAI API key:")
        print("  export OPENAI_API_KEY=your_key_here")
        return False


def main():
    """Run the setup process."""
    print("\n" + "="*80)
    print("MLflow Evaluation Framework Setup")
    print("="*80)
    
    steps = [
        ("Docker Check", check_docker),
        ("OpenAI API Key Check", check_openai_key),
        ("Start MLflow Stack", start_mlflow_stack),
        ("Generate Test Dataset", generate_dataset),
    ]
    
    results = []
    for step_name, step_func in steps:
        success = step_func()
        results.append((step_name, success))
        
        if not success and step_name in ["Docker Check", "Start MLflow Stack"]:
            print(f"\n✗ Cannot continue without {step_name}")
            break
    
    # Print summary
    print("\n" + "="*80)
    print("Setup Summary")
    print("="*80)
    for step_name, success in results:
        status = "✓" if success else "✗"
        print(f"{status} {step_name}")
    
    all_success = all(success for _, success in results)
    
    if all_success:
        print("\n✓ Setup complete! You're ready to run evaluations.")
        print("\nNext steps:")
        print("1. View MLflow UI at http://localhost:5000")
        print("2. Run evaluation: python -m evaluations.harness")
    else:
        print("\n✗ Setup incomplete. Please fix the errors above.")
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
