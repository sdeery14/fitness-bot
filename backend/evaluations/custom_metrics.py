"""Custom metrics for AI agent evaluation.

These metrics measure latency, cost, and tool usage correctness.
"""
import time
from typing import Any, Callable
import tiktoken
from functools import wraps


# OpenAI pricing per 1M tokens (as of Dec 2024)
PRICING = {
    "gpt-4o": {
        "input": 2.50,  # per 1M input tokens
        "output": 10.00  # per 1M output tokens
    },
    "gpt-4o-mini": {
        "input": 0.150,
        "output": 0.600
    },
    "gpt-4-turbo": {
        "input": 10.00,
        "output": 30.00
    }
}


class MetricsCollector:
    """Collects custom metrics during agent execution."""
    
    def __init__(self):
        self.metrics = {
            "latency_ms": 0,
            "total_cost_usd": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "tool_calls": [],
            "tool_call_count": 0,
            "correct_tool_calls": 0,
            "incorrect_tool_calls": 0,
        }
        self.start_time = None
        self.encoding = tiktoken.encoding_for_model("gpt-4o")
    
    def start_timer(self):
        """Start the latency timer."""
        self.start_time = time.time()
    
    def stop_timer(self):
        """Stop the latency timer and record elapsed time."""
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.metrics["latency_ms"] = int(elapsed * 1000)
    
    def record_llm_call(
        self,
        model: str,
        input_text: str,
        output_text: str
    ):
        """Record token usage and cost for an LLM call."""
        input_tokens = len(self.encoding.encode(input_text))
        output_tokens = len(self.encoding.encode(output_text))
        
        self.metrics["input_tokens"] += input_tokens
        self.metrics["output_tokens"] += output_tokens
        
        # Calculate cost
        model_key = model.split("/")[-1]  # Handle "openai/gpt-4o" format
        if model_key in PRICING:
            pricing = PRICING[model_key]
            input_cost = (input_tokens / 1_000_000) * pricing["input"]
            output_cost = (output_tokens / 1_000_000) * pricing["output"]
            self.metrics["total_cost_usd"] += input_cost + output_cost
    
    def record_tool_call(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        is_correct: bool,
        expected_tool: str | None = None,
        error: str | None = None
    ):
        """Record a tool call and whether it was correct."""
        self.metrics["tool_calls"].append({
            "tool_name": tool_name,
            "parameters": parameters,
            "is_correct": is_correct,
            "expected_tool": expected_tool,
            "error": error
        })
        self.metrics["tool_call_count"] += 1
        
        if is_correct:
            self.metrics["correct_tool_calls"] += 1
        else:
            self.metrics["incorrect_tool_calls"] += 1
    
    def get_metrics(self) -> dict[str, Any]:
        """Get all collected metrics."""
        # Calculate derived metrics
        if self.metrics["tool_call_count"] > 0:
            self.metrics["tool_call_accuracy"] = (
                self.metrics["correct_tool_calls"] / self.metrics["tool_call_count"]
            )
        else:
            self.metrics["tool_call_accuracy"] = 0.0
        
        # Cost per 1K tokens (useful for comparison)
        total_tokens = self.metrics["input_tokens"] + self.metrics["output_tokens"]
        if total_tokens > 0:
            self.metrics["cost_per_1k_tokens"] = (
                self.metrics["total_cost_usd"] / (total_tokens / 1000)
            )
        else:
            self.metrics["cost_per_1k_tokens"] = 0.0
        
        return self.metrics


def calculate_tool_usage_score(
    tool_calls: list[dict[str, Any]],
    expected_tools: list[str]
) -> dict[str, Any]:
    """Calculate tool usage correctness score.
    
    Args:
        tool_calls: List of actual tool calls made by agent
        expected_tools: List of expected tool names
    
    Returns:
        Dictionary with score and analysis
    """
    if not tool_calls:
        return {
            "score": 0.0,
            "analysis": "No tools were called",
            "correct_tools": [],
            "missing_tools": expected_tools,
            "unexpected_tools": []
        }
    
    actual_tools = [call["tool_name"] for call in tool_calls]
    correct_tools = [tool for tool in actual_tools if tool in expected_tools]
    missing_tools = [tool for tool in expected_tools if tool not in actual_tools]
    unexpected_tools = [tool for tool in actual_tools if tool not in expected_tools]
    
    # Calculate score
    # Correct tools: +1 point each
    # Missing tools: -1 point each
    # Unexpected tools: -0.5 points each (less severe than missing)
    score = len(correct_tools) - len(missing_tools) - (0.5 * len(unexpected_tools))
    max_score = len(expected_tools)
    normalized_score = max(0.0, min(1.0, score / max_score if max_score > 0 else 0.0))
    
    return {
        "score": normalized_score,
        "analysis": f"{len(correct_tools)}/{len(expected_tools)} expected tools called",
        "correct_tools": correct_tools,
        "missing_tools": missing_tools,
        "unexpected_tools": unexpected_tools
    }


def calculate_parameter_correctness(
    tool_call: dict[str, Any],
    expected_parameters: dict[str, Any]
) -> dict[str, Any]:
    """Calculate how well tool parameters match expectations.
    
    Args:
        tool_call: Actual tool call with parameters
        expected_parameters: Expected parameter structure
    
    Returns:
        Dictionary with score and analysis
    """
    actual_params = tool_call.get("parameters", {})
    
    if not expected_parameters:
        return {
            "score": 1.0,
            "analysis": "No parameter validation specified",
            "correct_params": list(actual_params.keys()),
            "missing_params": [],
            "incorrect_params": []
        }
    
    correct_params = []
    missing_params = []
    incorrect_params = []
    
    for param_name, expected_value in expected_parameters.items():
        if param_name not in actual_params:
            missing_params.append(param_name)
        elif callable(expected_value):
            # Custom validation function
            if expected_value(actual_params[param_name]):
                correct_params.append(param_name)
            else:
                incorrect_params.append(param_name)
        elif expected_value == actual_params[param_name]:
            correct_params.append(param_name)
        else:
            incorrect_params.append(param_name)
    
    # Calculate score
    total_params = len(expected_parameters)
    score = len(correct_params) / total_params if total_params > 0 else 1.0
    
    return {
        "score": score,
        "analysis": f"{len(correct_params)}/{total_params} parameters correct",
        "correct_params": correct_params,
        "missing_params": missing_params,
        "incorrect_params": incorrect_params
    }


class LatencyMetric:
    """Metric for measuring execution latency."""
    
    @staticmethod
    def calculate(metrics: dict[str, Any]) -> dict[str, Any]:
        """Calculate latency statistics."""
        latency_ms = metrics.get("latency_ms", 0)
        
        # Categorize latency
        if latency_ms < 1000:
            category = "excellent"
        elif latency_ms < 3000:
            category = "good"
        elif latency_ms < 5000:
            category = "acceptable"
        elif latency_ms < 10000:
            category = "slow"
        else:
            category = "very_slow"
        
        return {
            "latency_ms": latency_ms,
            "latency_seconds": latency_ms / 1000,
            "category": category
        }


class CostMetric:
    """Metric for measuring API cost."""
    
    @staticmethod
    def calculate(metrics: dict[str, Any]) -> dict[str, Any]:
        """Calculate cost statistics."""
        total_cost = metrics.get("total_cost_usd", 0.0)
        input_tokens = metrics.get("input_tokens", 0)
        output_tokens = metrics.get("output_tokens", 0)
        total_tokens = input_tokens + output_tokens
        
        # Categorize cost
        if total_cost < 0.01:
            category = "very_cheap"
        elif total_cost < 0.05:
            category = "cheap"
        elif total_cost < 0.10:
            category = "moderate"
        elif total_cost < 0.25:
            category = "expensive"
        else:
            category = "very_expensive"
        
        return {
            "total_cost_usd": round(total_cost, 4),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_per_1k_tokens": metrics.get("cost_per_1k_tokens", 0.0),
            "category": category
        }


class ToolUsageMetric:
    """Metric for measuring tool usage correctness."""
    
    @staticmethod
    def calculate(metrics: dict[str, Any]) -> dict[str, Any]:
        """Calculate tool usage statistics."""
        tool_calls = metrics.get("tool_calls", [])
        correct_calls = metrics.get("correct_tool_calls", 0)
        incorrect_calls = metrics.get("incorrect_tool_calls", 0)
        total_calls = metrics.get("tool_call_count", 0)
        
        accuracy = metrics.get("tool_call_accuracy", 0.0)
        
        # Categorize accuracy
        if accuracy >= 0.95:
            category = "excellent"
        elif accuracy >= 0.85:
            category = "good"
        elif accuracy >= 0.70:
            category = "acceptable"
        elif accuracy >= 0.50:
            category = "poor"
        else:
            category = "very_poor"
        
        return {
            "tool_call_count": total_calls,
            "correct_calls": correct_calls,
            "incorrect_calls": incorrect_calls,
            "accuracy": round(accuracy, 3),
            "category": category,
            "tool_calls": tool_calls
        }


def compute_all_custom_metrics(collector: MetricsCollector) -> dict[str, Any]:
    """Compute all custom metrics from collector.
    
    Args:
        collector: MetricsCollector instance with recorded data
    
    Returns:
        Dictionary with all computed metrics
    """
    metrics = collector.get_metrics()
    
    return {
        "latency": LatencyMetric.calculate(metrics),
        "cost": CostMetric.calculate(metrics),
        "tool_usage": ToolUsageMetric.calculate(metrics)
    }
