"""
Data models for the persona simulation framework.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Role of an agent in the conversation."""
    INTERVIEWER = "interviewer"
    INTERVIEWEE = "interviewee"


class MessageType(str, Enum):
    """Type of message in the conversation."""
    TEXT = "text"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    THINKING = "thinking"


class Message(BaseModel):
    """A single message in a conversation."""
    role: AgentRole
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Persona(BaseModel):
    """Definition of a persona for an agent."""
    name: str
    description: str
    background: str
    goals: List[str]
    pain_points: List[str]
    communication_style: str
    technical_level: str  # e.g., "beginner", "intermediate", "expert"
    key_characteristics: List[str]
    objections: List[str] = Field(default_factory=list)
    priorities: List[str] = Field(default_factory=list)

    def to_prompt(self) -> str:
        """Convert persona to a prompt string."""
        return f"""You are roleplaying as: {self.name}

Background: {self.background}

Description: {self.description}

Goals:
{chr(10).join(f"- {goal}" for goal in self.goals)}

Pain Points:
{chr(10).join(f"- {pain}" for pain in self.pain_points)}

Communication Style: {self.communication_style}

Technical Level: {self.technical_level}

Key Characteristics:
{chr(10).join(f"- {char}" for char in self.key_characteristics)}

{f"Common Objections:{chr(10)}{chr(10).join(f'- {obj}' for obj in self.objections)}" if self.objections else ""}

{f"Priorities:{chr(10)}{chr(10).join(f'- {pri}' for pri in self.priorities)}" if self.priorities else ""}

Stay in character throughout the conversation. Your responses should reflect this persona's perspective, knowledge level, and communication style."""


class CommunicationStrategy(BaseModel):
    """Strategy for how the interviewer should communicate."""
    name: str
    description: str
    key_points: List[str]
    approach: str
    dos: List[str]
    donts: List[str]
    target_outcomes: List[str]
    emphasis_areas: List[str] = Field(default_factory=list)
    example_phrases: List[str] = Field(default_factory=list)

    def to_prompt(self) -> str:
        """Convert strategy to a prompt string."""
        return f"""Communication Strategy: {self.name}

Description: {self.description}

Approach: {self.approach}

Key Points to Cover:
{chr(10).join(f"- {point}" for point in self.key_points)}

DO:
{chr(10).join(f"- {do}" for do in self.dos)}

DON'T:
{chr(10).join(f"- {dont}" for dont in self.donts)}

Target Outcomes:
{chr(10).join(f"- {outcome}" for outcome in self.target_outcomes)}

{f"Areas to Emphasize:{chr(10)}{chr(10).join(f'- {area}' for area in self.emphasis_areas)}" if self.emphasis_areas else ""}

{f"Example Phrases:{chr(10)}{chr(10).join(f'- \"{phrase}\"' for phrase in self.example_phrases)}" if self.example_phrases else ""}"""


class ConversationConfig(BaseModel):
    """Configuration for a conversation simulation."""
    max_turns: int = 20
    interviewer_persona: Optional[Persona] = None
    interviewee_persona: Persona
    strategy: CommunicationStrategy
    product_name: str
    product_description: str
    knowledge_base_path: Optional[str] = None
    temperature: float = 0.7
    model: str = "claude-sonnet-4-5-20250929"


class Conversation(BaseModel):
    """A complete conversation between interviewer and interviewee."""
    id: str
    config: ConversationConfig
    messages: List[Message] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def add_message(self, message: Message):
        """Add a message to the conversation."""
        self.messages.append(message)

    def get_turn_count(self) -> int:
        """Get the current turn count."""
        return len([m for m in self.messages if m.message_type == MessageType.TEXT])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return self.model_dump()


class QuestionnaireQuestion(BaseModel):
    """A single question in the questionnaire."""
    id: str
    question: str
    expected_answer: Optional[str] = None
    category: str  # e.g., "understanding", "interest", "objections"
    weight: float = 1.0


class Questionnaire(BaseModel):
    """Post-conversation questionnaire."""
    questions: List[QuestionnaireQuestion]
    product_name: str

    def to_prompt(self) -> str:
        """Convert questionnaire to a prompt."""
        questions_text = "\n\n".join(
            f"{i+1}. {q.question}\n   Category: {q.category}"
            for i, q in enumerate(self.questions)
        )
        return f"""Based on the conversation you just had about {self.product_name}, please answer the following questions honestly from your persona's perspective:

{questions_text}

Please provide detailed answers that reflect your persona's understanding, perspective, and level of interest."""


class QuestionnaireResponse(BaseModel):
    """Response to a questionnaire."""
    conversation_id: str
    answers: Dict[str, str]  # question_id -> answer
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EvaluationCriteria(BaseModel):
    """Criteria for evaluating a conversation."""
    name: str
    description: str
    weight: float = 1.0


class EvaluationScore(BaseModel):
    """Score for a single evaluation criterion."""
    criterion: str
    score: float  # 0-100
    reasoning: str
    evidence: List[str] = Field(default_factory=list)


class InterviewerEvaluation(BaseModel):
    """Evaluation of the interviewer's performance."""
    conversation_id: str
    strategy_adherence_score: float  # 0-100
    strategy_adherence_reasoning: str
    individual_scores: List[EvaluationScore]
    overall_score: float  # weighted average
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class IntervieweeEvaluation(BaseModel):
    """Evaluation of the interviewee's performance."""
    conversation_id: str
    persona_adherence_score: float  # 0-100
    persona_adherence_reasoning: str
    questionnaire_score: float  # 0-100
    questionnaire_reasoning: str
    overall_score: float
    consistency_issues: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SimulationResult(BaseModel):
    """Complete result of a conversation simulation."""
    conversation: Conversation
    questionnaire_response: QuestionnaireResponse
    interviewer_eval: InterviewerEvaluation
    interviewee_eval: IntervieweeEvaluation
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return self.model_dump()


class OptimizationMetrics(BaseModel):
    """Metrics tracked during optimization."""
    iteration: int
    avg_interviewer_score: float
    avg_interviewee_understanding_score: float
    avg_overall_effectiveness: float
    strategy_version: str
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OptimizationResult(BaseModel):
    """Result of strategy optimization."""
    initial_strategy: CommunicationStrategy
    optimized_strategy: CommunicationStrategy
    metrics_history: List[OptimizationMetrics]
    improvement_percentage: float
    best_iteration: int
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
