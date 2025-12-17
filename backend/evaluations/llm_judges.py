"""LLM-as-a-Judge evaluators for AI agent evaluation.

These evaluators use GPT-4 to judge the quality of agent outputs across
multiple dimensions: output quality, tool selection, response quality, and safety.
"""

import os
from typing import Any
import mlflow
from openai import AsyncOpenAI


class LLMJudge:
    """Base class for LLM-as-a-judge evaluators."""

    def __init__(self, model: str = "gpt-4o", temperature: float = 0.2):
        """Initialize the LLM judge.

        Args:
            model: OpenAI model to use for judging
            temperature: Lower temperature for more consistent judgments
        """
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.temperature = temperature

    async def judge(
        self,
        input_data: dict[str, Any],
        agent_output: dict[str, Any],
        expected_output: dict[str, Any],
        criteria: dict[str, Any],
    ) -> dict[str, Any]:
        """Judge the agent output.

        Returns:
            Dictionary with score (0-1) and reasoning for the judgment
        """
        raise NotImplementedError


class OutputQualityJudge(LLMJudge):
    """Evaluates the quality and appropriateness of agent output."""

    async def judge(
        self,
        input_data: dict[str, Any],
        agent_output: dict[str, Any],
        expected_output: dict[str, Any],
        criteria: dict[str, Any],
    ) -> dict[str, Any]:
        """Judge output quality based on fitness/workout appropriateness."""

        aspects = criteria.get("aspects", [])
        aspects_str = "\n".join(f"- {aspect}" for aspect in aspects)

        prompt = f"""You are an expert fitness professional evaluating a workout generation system.

INPUT REQUIREMENTS:
User Profile:
- Fitness Level: {input_data.get('user_profile', {}).get('fitness_level')}
- Equipment: {input_data.get('user_profile', {}).get('equipment')}
- Experience: {input_data.get('user_profile', {}).get('experience_years')} years
- Injuries: {input_data.get('user_profile', {}).get('injuries', [])}

Phase Details:
- Name: {input_data.get('phase_name')}
- Duration: {input_data.get('duration_weeks')} weeks
- Objectives: {', '.join(input_data.get('objectives', []))}

Preferences:
- Frequency: {input_data.get('workout_preferences', {}).get('frequency_per_week')} days/week
- Duration: {input_data.get('workout_preferences', {}).get('duration_minutes')} minutes

AGENT OUTPUT:
{agent_output}

EVALUATION CRITERIA:
Judge the output quality based on these aspects:
{aspects_str}

EXPECTED OUTPUT CHARACTERISTICS:
{expected_output}

Rate the output quality on a scale of 0.0 to 1.0, where:
- 1.0 = Perfect: All aspects met, workout is expertly designed
- 0.8 = Good: Most aspects met, minor improvements possible
- 0.6 = Acceptable: Core aspects met, some notable issues
- 0.4 = Poor: Multiple significant issues
- 0.2 = Very Poor: Major problems with safety or appropriateness
- 0.0 = Unacceptable: Completely inappropriate or unsafe

Provide your response in this exact format:
SCORE: [your score as a decimal between 0.0 and 1.0]
REASONING: [2-3 sentences explaining your score, referencing specific aspects]
STRENGTHS: [bullet points of what was done well]
IMPROVEMENTS: [bullet points of what could be better]
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content
        return self._parse_judgment(content)

    def _parse_judgment(self, content: str) -> dict[str, Any]:
        """Parse the LLM's judgment response."""
        lines = content.strip().split("\n")
        result = {"score": 0.0, "reasoning": "", "strengths": [], "improvements": []}

        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith("SCORE:"):
                try:
                    result["score"] = float(line.replace("SCORE:", "").strip())
                except ValueError:
                    result["score"] = 0.0
            elif line.startswith("REASONING:"):
                result["reasoning"] = line.replace("REASONING:", "").strip()
            elif line.startswith("STRENGTHS:"):
                current_section = "strengths"
            elif line.startswith("IMPROVEMENTS:"):
                current_section = "improvements"
            elif line.startswith("- ") and current_section:
                result[current_section].append(line[2:])

        return result


class ToolSelectionJudge(LLMJudge):
    """Evaluates whether the agent selected and used tools correctly."""

    async def judge(
        self,
        input_data: dict[str, Any],
        agent_output: dict[str, Any],
        expected_output: dict[str, Any],
        criteria: dict[str, Any],
    ) -> dict[str, Any]:
        """Judge tool selection correctness."""

        aspects = criteria.get("aspects", [])
        aspects_str = "\n".join(f"- {aspect}" for aspect in aspects)

        # Extract tool usage from agent output
        tools_used = agent_output.get("tools_used", [])
        tool_params = agent_output.get("tool_parameters", {})

        prompt = f"""You are evaluating an AI agent's tool usage in a fitness planning system.

USER REQUEST:
{input_data}

TOOLS USED BY AGENT:
{tools_used}

TOOL PARAMETERS:
{tool_params}

EVALUATION CRITERIA:
{aspects_str}

EXPECTED BEHAVIOR:
{expected_output}

Rate the tool selection on a scale of 0.0 to 1.0, where:
- 1.0 = Perfect: Correct tools, all parameters valid and optimal
- 0.8 = Good: Correct tools, parameters valid with minor suboptimal choices
- 0.6 = Acceptable: Correct tools but some parameter issues
- 0.4 = Poor: Wrong tools or significant parameter errors
- 0.2 = Very Poor: Major tool misuse
- 0.0 = Unacceptable: Completely wrong tool selection or critical errors

Provide your response in this exact format:
SCORE: [your score as a decimal between 0.0 and 1.0]
REASONING: [2-3 sentences explaining your score]
CORRECT: [what was done correctly]
INCORRECT: [what was done incorrectly, if anything]
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content
        return self._parse_judgment(content)

    def _parse_judgment(self, content: str) -> dict[str, Any]:
        """Parse the LLM's judgment response."""
        lines = content.strip().split("\n")
        result = {"score": 0.0, "reasoning": "", "correct": "", "incorrect": ""}

        for line in lines:
            line = line.strip()
            if line.startswith("SCORE:"):
                try:
                    result["score"] = float(line.replace("SCORE:", "").strip())
                except ValueError:
                    result["score"] = 0.0
            elif line.startswith("REASONING:"):
                result["reasoning"] = line.replace("REASONING:", "").strip()
            elif line.startswith("CORRECT:"):
                result["correct"] = line.replace("CORRECT:", "").strip()
            elif line.startswith("INCORRECT:"):
                result["incorrect"] = line.replace("INCORRECT:", "").strip()

        return result


class ResponseQualityJudge(LLMJudge):
    """Evaluates the quality of the agent's conversational response."""

    async def judge(
        self,
        input_data: dict[str, Any],
        agent_output: dict[str, Any],
        expected_output: dict[str, Any],
        criteria: dict[str, Any],
    ) -> dict[str, Any]:
        """Judge response quality (clarity, helpfulness, tone)."""

        aspects = criteria.get("aspects", [])
        aspects_str = "\n".join(f"- {aspect}" for aspect in aspects)

        response_text = agent_output.get("response_text", "")

        prompt = f"""You are evaluating the quality of an AI fitness coach's response to a user.

USER CONTEXT:
{input_data}

AGENT'S RESPONSE:
{response_text}

EVALUATION CRITERIA:
{aspects_str}

Rate the response quality on a scale of 0.0 to 1.0, where:
- 1.0 = Excellent: Clear, helpful, perfectly appropriate tone
- 0.8 = Good: Clear and helpful with minor areas for improvement
- 0.6 = Acceptable: Adequate but could be clearer or more helpful
- 0.4 = Poor: Unclear or unhelpful in significant ways
- 0.2 = Very Poor: Confusing or inappropriate
- 0.0 = Unacceptable: Completely unhelpful or inappropriate

Provide your response in this exact format:
SCORE: [your score as a decimal between 0.0 and 1.0]
REASONING: [2-3 sentences explaining your score]
TONE: [assessment of the conversational tone]
CLARITY: [assessment of how clear and understandable it is]
HELPFULNESS: [assessment of how helpful it is to the user]
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content
        return self._parse_judgment(content)

    def _parse_judgment(self, content: str) -> dict[str, Any]:
        """Parse the LLM's judgment response."""
        lines = content.strip().split("\n")
        result = {"score": 0.0, "reasoning": "", "tone": "", "clarity": "", "helpfulness": ""}

        for line in lines:
            line = line.strip()
            if line.startswith("SCORE:"):
                try:
                    result["score"] = float(line.replace("SCORE:", "").strip())
                except ValueError:
                    result["score"] = 0.0
            elif line.startswith("REASONING:"):
                result["reasoning"] = line.replace("REASONING:", "").strip()
            elif line.startswith("TONE:"):
                result["tone"] = line.replace("TONE:", "").strip()
            elif line.startswith("CLARITY:"):
                result["clarity"] = line.replace("CLARITY:", "").strip()
            elif line.startswith("HELPFULNESS:"):
                result["helpfulness"] = line.replace("HELPFULNESS:", "").strip()

        return result


class SafetyJudge(LLMJudge):
    """Evaluates safety aspects of workout recommendations."""

    async def judge(
        self,
        input_data: dict[str, Any],
        agent_output: dict[str, Any],
        expected_output: dict[str, Any],
        criteria: dict[str, Any],
    ) -> dict[str, Any]:
        """Judge safety considerations."""

        aspects = criteria.get("aspects", [])
        aspects_str = "\n".join(f"- {aspect}" for aspect in aspects)

        injuries = input_data.get("user_profile", {}).get("injuries", [])
        fitness_level = input_data.get("user_profile", {}).get("fitness_level")

        prompt = f"""You are a fitness safety expert evaluating workout recommendations.

USER PROFILE:
- Fitness Level: {fitness_level}
- Injuries/Limitations: {injuries if injuries else "None reported"}
- Experience: {input_data.get('user_profile', {}).get('experience_years')} years

WORKOUT RECOMMENDATION:
{agent_output}

SAFETY CRITERIA:
{aspects_str}

Rate the safety on a scale of 0.0 to 1.0, where:
- 1.0 = Excellent: All safety considerations properly addressed
- 0.8 = Good: Safe with minor recommendations
- 0.6 = Acceptable: Generally safe but some concerns
- 0.4 = Concerning: Notable safety issues present
- 0.2 = Dangerous: Significant risk of injury
- 0.0 = Unacceptable: Seriously unsafe recommendations

Provide your response in this exact format:
SCORE: [your score as a decimal between 0.0 and 1.0]
REASONING: [2-3 sentences explaining your safety assessment]
SAFETY_STRENGTHS: [what safety considerations were done well]
SAFETY_CONCERNS: [any safety issues or risks identified]
INJURY_RISK: [assessment of injury risk: LOW/MEDIUM/HIGH]
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content
        return self._parse_judgment(content)

    def _parse_judgment(self, content: str) -> dict[str, Any]:
        """Parse the LLM's judgment response."""
        lines = content.strip().split("\n")
        result = {
            "score": 0.0,
            "reasoning": "",
            "safety_strengths": "",
            "safety_concerns": "",
            "injury_risk": "UNKNOWN",
        }

        for line in lines:
            line = line.strip()
            if line.startswith("SCORE:"):
                try:
                    result["score"] = float(line.replace("SCORE:", "").strip())
                except ValueError:
                    result["score"] = 0.0
            elif line.startswith("REASONING:"):
                result["reasoning"] = line.replace("REASONING:", "").strip()
            elif line.startswith("SAFETY_STRENGTHS:"):
                result["safety_strengths"] = line.replace("SAFETY_STRENGTHS:", "").strip()
            elif line.startswith("SAFETY_CONCERNS:"):
                result["safety_concerns"] = line.replace("SAFETY_CONCERNS:", "").strip()
            elif line.startswith("INJURY_RISK:"):
                result["injury_risk"] = line.replace("INJURY_RISK:", "").strip()

        return result


async def evaluate_with_judges(
    input_data: dict[str, Any],
    agent_output: dict[str, Any],
    expected_output: dict[str, Any],
    evaluation_criteria: dict[str, Any],
) -> dict[str, Any]:
    """Run all LLM judges and compute weighted score.

    Returns:
        Dictionary with overall score and individual judge results
    """
    judges = {
        "output_quality": OutputQualityJudge(),
        "tool_selection": ToolSelectionJudge(),
        "response_quality": ResponseQualityJudge(),
        "safety": SafetyJudge(),
    }

    results = {}
    weighted_score = 0.0

    for criterion_name, judge in judges.items():
        if criterion_name in evaluation_criteria:
            criteria = evaluation_criteria[criterion_name]
            weight = criteria.get("weight", 0.25)

            judgment = await judge.judge(
                input_data=input_data,
                agent_output=agent_output,
                expected_output=expected_output,
                criteria=criteria,
            )

            results[criterion_name] = judgment
            weighted_score += judgment["score"] * weight

    return {"overall_score": weighted_score, "individual_scores": results}
