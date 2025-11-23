"""
LLM-as-a-judge evaluation system for scoring conversations.
"""

import os
import json
import logging
from typing import Optional, List, Dict
from anthropic import Anthropic

from ..models import (
    Conversation,
    Persona,
    CommunicationStrategy,
    QuestionnaireResponse,
    Questionnaire,
    InterviewerEvaluation,
    IntervieweeEvaluation,
    EvaluationScore,
)

logger = logging.getLogger(__name__)


class ConversationJudge:
    """
    LLM-based judge for evaluating conversation quality and adherence.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-5-20250929",
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize the conversation judge.

        Args:
            model: Anthropic model to use
            anthropic_api_key: API key for Anthropic
        """
        self.model = model

        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        self.client = Anthropic(api_key=api_key)

    def evaluate_interviewer(
        self,
        conversation: Conversation,
        strategy: CommunicationStrategy,
        ground_truth_conversations: Optional[List[str]] = None,
    ) -> InterviewerEvaluation:
        """
        Evaluate the interviewer's performance.

        Args:
            conversation: The conversation to evaluate
            strategy: The communication strategy that should have been followed
            ground_truth_conversations: Optional examples of good conversations

        Returns:
            Interviewer evaluation
        """
        # Build conversation history
        conv_history = "\n\n".join(
            f"{'Interviewer' if msg.role.value == 'interviewer' else 'Interviewee'}: {msg.content}"
            for msg in conversation.messages
        )

        prompt = f"""You are an expert evaluator of sales and communication strategies. You need to evaluate how well an interviewer followed a specific communication strategy in a conversation.

COMMUNICATION STRATEGY TO FOLLOW:
{strategy.to_prompt()}

CONVERSATION:
{conv_history}

---

Please evaluate the interviewer's performance on the following criteria:

1. **Strategy Adherence** (0-100): How well did they follow the prescribed strategy?
   - Did they cover the key points?
   - Did they follow the DOs and avoid the DON'Ts?
   - Did they work towards the target outcomes?

2. **Clarity** (0-100): How clearly did they explain concepts?

3. **Responsiveness** (0-100): How well did they respond to the interviewee's questions and concerns?

4. **Persuasiveness** (0-100): How convincing were their arguments?

5. **Engagement** (0-100): How well did they maintain engagement and interest?

For each criterion, provide:
- A score (0-100)
- Brief reasoning
- Specific evidence (quote from conversation)

Also provide:
- Overall strengths (2-3 points)
- Overall weaknesses (2-3 points)
- Suggestions for improvement (2-3 points)

Format your response as JSON:
{{
  "strategy_adherence": {{
    "score": <number>,
    "reasoning": "<text>",
    "evidence": ["<quote1>", "<quote2>"]
  }},
  "clarity": {{
    "score": <number>,
    "reasoning": "<text>",
    "evidence": ["<quote1>"]
  }},
  "responsiveness": {{
    "score": <number>,
    "reasoning": "<text>",
    "evidence": ["<quote1>"]
  }},
  "persuasiveness": {{
    "score": <number>,
    "reasoning": "<text>",
    "evidence": ["<quote1>"]
  }},
  "engagement": {{
    "score": <number>,
    "reasoning": "<text>",
    "evidence": ["<quote1>"]
  }},
  "strengths": ["<strength1>", "<strength2>"],
  "weaknesses": ["<weakness1>", "<weakness2>"],
  "suggestions": ["<suggestion1>", "<suggestion2>"]
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text if response.content else ""

            # Parse JSON response
            eval_data = self._parse_json_response(content)

            # Create evaluation scores
            scores = []
            weights = {
                "strategy_adherence": 2.0,
                "clarity": 1.0,
                "responsiveness": 1.0,
                "persuasiveness": 1.5,
                "engagement": 1.0,
            }

            total_weight = 0
            weighted_sum = 0

            for criterion, weight in weights.items():
                if criterion in eval_data:
                    score_data = eval_data[criterion]
                    score = EvaluationScore(
                        criterion=criterion,
                        score=score_data.get("score", 0),
                        reasoning=score_data.get("reasoning", ""),
                        evidence=score_data.get("evidence", []),
                    )
                    scores.append(score)

                    weighted_sum += score.score * weight
                    total_weight += weight

            overall_score = weighted_sum / total_weight if total_weight > 0 else 0
            strategy_adherence_score = eval_data.get("strategy_adherence", {}).get("score", 0)

            return InterviewerEvaluation(
                conversation_id=conversation.id,
                strategy_adherence_score=strategy_adherence_score,
                strategy_adherence_reasoning=eval_data.get("strategy_adherence", {}).get(
                    "reasoning", ""
                ),
                individual_scores=scores,
                overall_score=overall_score,
                strengths=eval_data.get("strengths", []),
                weaknesses=eval_data.get("weaknesses", []),
                suggestions=eval_data.get("suggestions", []),
            )

        except Exception as e:
            logger.error(f"Error evaluating interviewer: {e}")
            raise

    def evaluate_interviewee(
        self,
        conversation: Conversation,
        persona: Persona,
        questionnaire_response: QuestionnaireResponse,
        questionnaire: Questionnaire,
    ) -> IntervieweeEvaluation:
        """
        Evaluate the interviewee's performance.

        Args:
            conversation: The conversation to evaluate
            persona: The persona that should have been maintained
            questionnaire_response: The questionnaire responses
            questionnaire: The questionnaire

        Returns:
            Interviewee evaluation
        """
        # Build conversation history
        conv_history = "\n\n".join(
            f"{'Interviewer' if msg.role.value == 'interviewer' else 'Interviewee'}: {msg.content}"
            for msg in conversation.messages
        )

        # Build questionnaire answers
        qa_text = "\n\n".join(
            f"Q: {q.question}\nA: {questionnaire_response.answers.get(q.id, 'No answer')}"
            for q in questionnaire.questions
        )

        prompt = f"""You are an expert evaluator of role-playing and persona adherence. You need to evaluate how well someone maintained a specific persona during a conversation.

PERSONA TO MAINTAIN:
{persona.to_prompt()}

CONVERSATION:
{conv_history}

QUESTIONNAIRE RESPONSES:
{qa_text}

---

Please evaluate the interviewee's performance on:

1. **Persona Adherence** (0-100): How consistently did they maintain the persona?
   - Did their responses match the persona's background and characteristics?
   - Was their communication style consistent with the persona?
   - Did they express appropriate technical understanding for their level?
   - Did they maintain the persona's goals, priorities, and concerns?

2. **Questionnaire Quality** (0-100): How well do their questionnaire answers reflect:
   - Understanding gained from the conversation
   - Consistency with their persona's perspective
   - Thoughtfulness and engagement with the topic
   - Realistic assessment of interest and concerns

Also identify:
- Any consistency issues or breaks in character (list specific examples)

Format your response as JSON:
{{
  "persona_adherence": {{
    "score": <number>,
    "reasoning": "<text>",
    "evidence": ["<quote1>", "<quote2>"]
  }},
  "questionnaire_quality": {{
    "score": <number>,
    "reasoning": "<text>"
  }},
  "consistency_issues": ["<issue1>", "<issue2>"]
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text if response.content else ""

            # Parse JSON response
            eval_data = self._parse_json_response(content)

            persona_score = eval_data.get("persona_adherence", {}).get("score", 0)
            questionnaire_score = eval_data.get("questionnaire_quality", {}).get("score", 0)

            # Overall score is weighted average (persona 60%, questionnaire 40%)
            overall_score = persona_score * 0.6 + questionnaire_score * 0.4

            return IntervieweeEvaluation(
                conversation_id=conversation.id,
                persona_adherence_score=persona_score,
                persona_adherence_reasoning=eval_data.get("persona_adherence", {}).get(
                    "reasoning", ""
                ),
                questionnaire_score=questionnaire_score,
                questionnaire_reasoning=eval_data.get("questionnaire_quality", {}).get(
                    "reasoning", ""
                ),
                overall_score=overall_score,
                consistency_issues=eval_data.get("consistency_issues", []),
            )

        except Exception as e:
            logger.error(f"Error evaluating interviewee: {e}")
            raise

    def _parse_json_response(self, content: str) -> dict:
        """
        Parse JSON response from LLM.

        Args:
            content: Response content

        Returns:
            Parsed dictionary
        """
        # Try to extract JSON from the response
        try:
            # Look for JSON block
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            return json.loads(json_str)

        except Exception as e:
            logger.warning(f"Error parsing JSON response: {e}")
            # Return empty dict if parsing fails
            return {}
