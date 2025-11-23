"""
Questionnaire system for evaluating interviewee understanding.
"""

import os
import logging
from typing import Optional, List, Dict
from anthropic import Anthropic

from ..models import (
    Questionnaire,
    QuestionnaireQuestion,
    QuestionnaireResponse,
    Conversation,
    Persona,
)

logger = logging.getLogger(__name__)


class QuestionnaireGenerator:
    """
    Generates questionnaires to assess interviewee's understanding and perspective.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-5-20250929",
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize the questionnaire generator.

        Args:
            model: Anthropic model to use
            anthropic_api_key: API key for Anthropic
        """
        self.model = model

        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        self.client = Anthropic(api_key=api_key)

    def generate_questionnaire(
        self,
        product_name: str,
        product_description: str,
        key_concepts: List[str],
        num_questions: int = 10,
    ) -> Questionnaire:
        """
        Generate a questionnaire for a product.

        Args:
            product_name: Name of the product
            product_description: Description of the product
            key_concepts: Key concepts to assess
            num_questions: Number of questions to generate

        Returns:
            Generated questionnaire
        """
        prompt = f"""Generate {num_questions} questionnaire questions to assess someone's understanding of {product_name} after a conversation about it.

Product Description: {product_description}

Key Concepts to Cover:
{chr(10).join(f"- {concept}" for concept in key_concepts)}

For each question, provide:
1. The question text
2. The category (one of: understanding, interest, objections, use_cases, technical_depth)
3. A brief expected answer (what would indicate good understanding)

Format each question as:
Q[number]: [question]
Category: [category]
Expected: [expected answer]

---

Generate questions that:
- Assess understanding of key features and concepts
- Gauge level of interest and likelihood to adopt
- Identify remaining objections or concerns
- Evaluate comprehension of use cases
- Test technical understanding appropriate to the conversation

Questions should be open-ended and encourage detailed responses."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text if response.content else ""

            # Parse the response into questions
            questions = self._parse_questions(content, product_name)

            return Questionnaire(
                questions=questions,
                product_name=product_name,
            )

        except Exception as e:
            logger.error(f"Error generating questionnaire: {e}")
            raise

    def _parse_questions(self, content: str, product_name: str) -> List[QuestionnaireQuestion]:
        """
        Parse generated questions from LLM response.

        Args:
            content: Generated content
            product_name: Name of the product

        Returns:
            List of questionnaire questions
        """
        questions = []
        current_q = {}

        for line in content.split("\n"):
            line = line.strip()

            if line.startswith("Q") and ":" in line:
                # Save previous question if exists
                if current_q:
                    questions.append(self._create_question(current_q, len(questions)))
                    current_q = {}

                # Start new question
                question_text = line.split(":", 1)[1].strip()
                current_q["question"] = question_text

            elif line.startswith("Category:"):
                category = line.split(":", 1)[1].strip()
                current_q["category"] = category

            elif line.startswith("Expected:"):
                expected = line.split(":", 1)[1].strip()
                current_q["expected_answer"] = expected

        # Add last question
        if current_q:
            questions.append(self._create_question(current_q, len(questions)))

        # If parsing failed, create default questions
        if not questions:
            questions = self._create_default_questions(product_name)

        return questions

    def _create_question(self, q_dict: dict, index: int) -> QuestionnaireQuestion:
        """Create a QuestionnaireQuestion from parsed data."""
        return QuestionnaireQuestion(
            id=f"q{index + 1}",
            question=q_dict.get("question", f"Question {index + 1}"),
            expected_answer=q_dict.get("expected_answer"),
            category=q_dict.get("category", "understanding"),
            weight=1.0,
        )

    def _create_default_questions(self, product_name: str) -> List[QuestionnaireQuestion]:
        """Create default questions if generation fails."""
        return [
            QuestionnaireQuestion(
                id="q1",
                question=f"What is your understanding of what {product_name} does?",
                category="understanding",
                weight=1.0,
            ),
            QuestionnaireQuestion(
                id="q2",
                question=f"What are the main benefits of {product_name} as you understand them?",
                category="understanding",
                weight=1.0,
            ),
            QuestionnaireQuestion(
                id="q3",
                question=f"How interested are you in using {product_name}? Why?",
                category="interest",
                weight=1.0,
            ),
            QuestionnaireQuestion(
                id="q4",
                question=f"What concerns or objections do you have about {product_name}?",
                category="objections",
                weight=1.0,
            ),
            QuestionnaireQuestion(
                id="q5",
                question=f"Can you describe a specific use case where {product_name} would be valuable?",
                category="use_cases",
                weight=1.0,
            ),
        ]


class QuestionnaireAdministrator:
    """
    Administers questionnaires to agents and collects responses.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-5-20250929",
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize the questionnaire administrator.

        Args:
            model: Anthropic model to use
            anthropic_api_key: API key for Anthropic
        """
        self.model = model

        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        self.client = Anthropic(api_key=api_key)

    def administer_questionnaire(
        self,
        questionnaire: Questionnaire,
        conversation: Conversation,
        persona: Persona,
    ) -> QuestionnaireResponse:
        """
        Administer a questionnaire to collect responses.

        Args:
            questionnaire: The questionnaire to administer
            conversation: The conversation that just occurred
            persona: The persona of the interviewee

        Returns:
            Questionnaire response
        """
        # Build conversation history
        conv_history = "\n\n".join(
            f"{'Interviewer' if msg.role.value == 'interviewer' else 'Interviewee'}: {msg.content}"
            for msg in conversation.messages
        )

        system_prompt = f"""{persona.to_prompt()}

You just had a conversation about {questionnaire.product_name}. Now you need to answer some questions about it.

IMPORTANT: Answer from your persona's perspective. Your answers should reflect:
- Your understanding based on what was discussed
- Your genuine level of interest (or lack thereof)
- Any concerns or objections you have
- Your technical comprehension level
- Your persona's priorities and goals

Be honest and authentic to your character."""

        user_message = f"""Here was the conversation you just had:

{conv_history}

---

{questionnaire.to_prompt()}

Please answer each question thoroughly, staying in character as {persona.name}."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            content = response.content[0].text if response.content else ""

            # Parse answers
            answers = self._parse_answers(content, questionnaire)

            return QuestionnaireResponse(
                conversation_id=conversation.id,
                answers=answers,
            )

        except Exception as e:
            logger.error(f"Error administering questionnaire: {e}")
            raise

    def _parse_answers(
        self,
        content: str,
        questionnaire: Questionnaire,
    ) -> Dict[str, str]:
        """
        Parse answers from the response.

        Args:
            content: Generated content
            questionnaire: The questionnaire

        Returns:
            Dictionary mapping question IDs to answers
        """
        answers = {}

        # Try to parse structured answers
        lines = content.split("\n")
        current_answer = []
        current_q_num = 0

        for line in lines:
            line = line.strip()

            # Check if this is a question number
            if line and line[0].isdigit() and "." in line:
                # Save previous answer
                if current_answer and current_q_num > 0:
                    q_id = questionnaire.questions[current_q_num - 1].id
                    answers[q_id] = " ".join(current_answer).strip()
                    current_answer = []

                # Extract question number
                try:
                    current_q_num = int(line.split(".")[0])
                    # Get answer text after the number
                    answer_text = line.split(".", 1)[1].strip() if "." in line else ""
                    if answer_text:
                        current_answer.append(answer_text)
                except:
                    if line:
                        current_answer.append(line)

            elif line:
                current_answer.append(line)

        # Save last answer
        if current_answer and current_q_num > 0 and current_q_num <= len(questionnaire.questions):
            q_id = questionnaire.questions[current_q_num - 1].id
            answers[q_id] = " ".join(current_answer).strip()

        # If parsing failed, use the whole content for first question
        if not answers and questionnaire.questions:
            answers[questionnaire.questions[0].id] = content

        return answers
