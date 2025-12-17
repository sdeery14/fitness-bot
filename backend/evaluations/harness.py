"""Evaluation harness for running agent evaluations with MLflow.

This script:
1. Loads evaluation datasets
2. Runs agents against test cases
3. Collects custom metrics (latency, cost, tool usage)
4. Runs LLM-as-a-judge evaluators
5. Logs everything to MLflow
"""
import os
import json
import asyncio
from pathlib import Path
from typing import Any
import mlflow
from mlflow import MlflowClient

from evaluations.custom_metrics import MetricsCollector, compute_all_custom_metrics
from evaluations.llm_judges import evaluate_with_judges
from evaluations.dataset_schema import EvaluationDataset, TestCase


class EvaluationHarness:
    """Harness for running agent evaluations."""
    
    def __init__(
        self,
        agent_runner: Any,  # Function that runs the agent
        experiment_name: str,
        mlflow_tracking_uri: str = "http://localhost:5000"
    ):
        """Initialize the evaluation harness.
        
        Args:
            agent_runner: Async function that runs the agent and returns output
            experiment_name: Name of the MLflow experiment
            mlflow_tracking_uri: URI of the MLflow tracking server
        """
        self.agent_runner = agent_runner
        self.experiment_name = experiment_name
        
        # Set up MLflow
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        mlflow.set_experiment(experiment_name)
        self.client = MlflowClient()
    
    async def run_single_test(
        self,
        test_case: TestCase,
        run_id: str
    ) -> dict[str, Any]:
        """Run a single test case and collect metrics.
        
        Args:
            test_case: The test case to run
            run_id: MLflow run ID for logging
        
        Returns:
            Dictionary with test results and metrics
        """
        print(f"\n{'='*80}")
        print(f"Running test case: {test_case.id}")
        print(f"Description: {test_case.description}")
        print(f"{'='*80}")
        
        # Initialize metrics collector
        collector = MetricsCollector()
        
        # Run the agent
        collector.start_timer()
        try:
            agent_output = await self.agent_runner(test_case.input, collector)
        except Exception as e:
            collector.stop_timer()
            return {
                "test_case_id": test_case.id,
                "status": "error",
                "error": str(e),
                "metrics": collector.get_metrics()
            }
        
        collector.stop_timer()
        
        # Compute custom metrics
        custom_metrics = compute_all_custom_metrics(collector)
        
        # Run LLM judges
        print(f"  Running LLM judges...")
        judge_results = await evaluate_with_judges(
            input_data=test_case.input,
            agent_output=agent_output,
            expected_output=test_case.expected_output,
            evaluation_criteria=test_case.evaluation_criteria
        )
        
        # Combine results
        result = {
            "test_case_id": test_case.id,
            "status": "success",
            "agent_output": agent_output,
            "custom_metrics": custom_metrics,
            "judge_scores": judge_results,
            "overall_score": judge_results["overall_score"]
        }
        
        # Log to MLflow
        with mlflow.start_run(run_id=run_id, nested=True):
            mlflow.set_tag("test_case_id", test_case.id)
            mlflow.set_tag("test_case_description", test_case.description)
            
            # Log custom metrics
            mlflow.log_metric("latency_ms", custom_metrics["latency"]["latency_ms"])
            mlflow.log_metric("cost_usd", custom_metrics["cost"]["total_cost_usd"])
            mlflow.log_metric("total_tokens", custom_metrics["cost"]["total_tokens"])
            mlflow.log_metric("tool_accuracy", custom_metrics["tool_usage"]["accuracy"])
            
            # Log judge scores
            mlflow.log_metric("overall_score", judge_results["overall_score"])
            for judge_name, judge_result in judge_results["individual_scores"].items():
                mlflow.log_metric(f"{judge_name}_score", judge_result["score"])
            
            # Log detailed results as artifacts
            artifact_dir = Path("tmp") / run_id / test_case.id
            artifact_dir.mkdir(parents=True, exist_ok=True)
            
            # Save agent output
            with open(artifact_dir / "agent_output.json", "w") as f:
                json.dump(agent_output, f, indent=2, default=str)
            
            # Save judge reasoning
            with open(artifact_dir / "judge_results.json", "w") as f:
                json.dump(judge_results, f, indent=2, default=str)
            
            # Save metrics
            with open(artifact_dir / "metrics.json", "w") as f:
                json.dump(custom_metrics, f, indent=2, default=str)
            
            mlflow.log_artifacts(str(artifact_dir))
        
        print(f"  ✓ Overall Score: {result['overall_score']:.3f}")
        print(f"  ✓ Latency: {custom_metrics['latency']['latency_ms']}ms")
        print(f"  ✓ Cost: ${custom_metrics['cost']['total_cost_usd']:.4f}")
        print(f"  ✓ Tool Accuracy: {custom_metrics['tool_usage']['accuracy']:.3f}")
        
        return result
    
    async def run_evaluation(
        self,
        dataset: EvaluationDataset,
        run_name: str | None = None
    ) -> dict[str, Any]:
        """Run evaluation on a dataset.
        
        Args:
            dataset: The evaluation dataset
            run_name: Optional name for the MLflow run
        
        Returns:
            Dictionary with aggregated results
        """
        print(f"\n{'='*80}")
        print(f"Starting Evaluation: {dataset.name} v{dataset.version}")
        print(f"Agent: {dataset.agent_name}")
        print(f"Test Cases: {len(dataset.test_cases)}")
        print(f"{'='*80}\n")
        
        # Start MLflow run
        with mlflow.start_run(run_name=run_name) as run:
            run_id = run.info.run_id
            
            # Log dataset metadata
            mlflow.set_tag("dataset_name", dataset.name)
            mlflow.set_tag("dataset_version", dataset.version)
            mlflow.set_tag("agent_name", dataset.agent_name)
            mlflow.log_param("num_test_cases", len(dataset.test_cases))
            
            # Run all test cases
            results = []
            for test_case in dataset.test_cases:
                result = await self.run_single_test(test_case, run_id)
                results.append(result)
            
            # Compute aggregate metrics
            successful_results = [r for r in results if r["status"] == "success"]
            
            if successful_results:
                avg_score = sum(r["overall_score"] for r in successful_results) / len(successful_results)
                avg_latency = sum(r["custom_metrics"]["latency"]["latency_ms"] for r in successful_results) / len(successful_results)
                avg_cost = sum(r["custom_metrics"]["cost"]["total_cost_usd"] for r in successful_results) / len(successful_results)
                avg_tool_accuracy = sum(r["custom_metrics"]["tool_usage"]["accuracy"] for r in successful_results) / len(successful_results)
                
                # Log aggregate metrics
                mlflow.log_metric("avg_overall_score", avg_score)
                mlflow.log_metric("avg_latency_ms", avg_latency)
                mlflow.log_metric("avg_cost_usd", avg_cost)
                mlflow.log_metric("avg_tool_accuracy", avg_tool_accuracy)
                
                # Compute per-judge averages
                judge_names = list(successful_results[0]["judge_scores"]["individual_scores"].keys())
                for judge_name in judge_names:
                    avg_judge_score = sum(
                        r["judge_scores"]["individual_scores"][judge_name]["score"]
                        for r in successful_results
                    ) / len(successful_results)
                    mlflow.log_metric(f"avg_{judge_name}_score", avg_judge_score)
                
                print(f"\n{'='*80}")
                print(f"Evaluation Complete!")
                print(f"{'='*80}")
                print(f"Successful: {len(successful_results)}/{len(results)} test cases")
                print(f"Average Score: {avg_score:.3f}")
                print(f"Average Latency: {avg_latency:.0f}ms")
                print(f"Average Cost: ${avg_cost:.4f}")
                print(f"Average Tool Accuracy: {avg_tool_accuracy:.3f}")
                print(f"{'='*80}\n")
                
                return {
                    "run_id": run_id,
                    "status": "success",
                    "total_tests": len(results),
                    "successful_tests": len(successful_results),
                    "failed_tests": len(results) - len(successful_results),
                    "avg_score": avg_score,
                    "avg_latency_ms": avg_latency,
                    "avg_cost_usd": avg_cost,
                    "avg_tool_accuracy": avg_tool_accuracy,
                    "detailed_results": results
                }
            else:
                print(f"\n✗ All test cases failed!")
                return {
                    "run_id": run_id,
                    "status": "all_failed",
                    "total_tests": len(results),
                    "successful_tests": 0,
                    "failed_tests": len(results),
                    "detailed_results": results
                }


def load_dataset(dataset_path: str | Path) -> EvaluationDataset:
    """Load an evaluation dataset from JSON file.
    
    Args:
        dataset_path: Path to the dataset JSON file
    
    Returns:
        EvaluationDataset instance
    """
    with open(dataset_path, "r") as f:
        data = json.load(f)
    
    # Reconstruct dataset from JSON
    from evaluations.workout_phase_dataset import workout_phase_dataset
    
    # For now, return the hardcoded dataset
    # In future, could dynamically construct from JSON
    return workout_phase_dataset


async def main():
    """Example usage of the evaluation harness."""
    from evaluations.workout_phase_dataset import workout_phase_dataset
    
    # Mock agent runner for testing
    async def mock_agent_runner(input_data: dict[str, Any], collector: MetricsCollector) -> dict[str, Any]:
        """Mock agent that generates dummy output."""
        await asyncio.sleep(0.5)  # Simulate processing time
        
        # Record mock LLM call
        collector.record_llm_call(
            model="gpt-4o",
            input_text=json.dumps(input_data),
            output_text="Generated workout phase"
        )
        
        # Record mock tool call
        collector.record_tool_call(
            tool_name="generate_workout_phase",
            parameters=input_data,
            is_correct=True
        )
        
        return {
            "phase_name": input_data.get("phase_name"),
            "workouts_generated": 3,
            "response_text": f"I've created a {input_data.get('phase_name')} phase for you.",
            "tools_used": ["generate_workout_phase"],
            "tool_parameters": input_data
        }
    
    # Create evaluation harness
    harness = EvaluationHarness(
        agent_runner=mock_agent_runner,
        experiment_name="workout_phase_agent_eval",
        mlflow_tracking_uri="http://localhost:5000"
    )
    
    # Run evaluation
    results = await harness.run_evaluation(
        dataset=workout_phase_dataset,
        run_name="baseline_evaluation"
    )
    
    print(f"\nResults saved to MLflow run: {results['run_id']}")
    print(f"View at: http://localhost:5000")


if __name__ == "__main__":
    asyncio.run(main())
