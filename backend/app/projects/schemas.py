"""Project API schemas."""
from typing import Optional, Union

from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    research_objectives: Optional[str] = None
    target_audience: Optional[str] = None
    language: str = Field(default="en", pattern="^(en|de)$")
    modality: str = Field(default="text", pattern="^(text|voice|hybrid)$")


class UpdateProjectRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    research_objectives: Optional[str] = None
    target_audience: Optional[str] = None
    language: Optional[str] = Field(None, pattern="^(en|de)$")
    modality: Optional[str] = Field(None, pattern="^(text|voice|hybrid)$")


QUESTION_TYPES = ("open", "multiple_choice", "scale", "ranking", "branching_gate")


class CreateQuestionRequest(BaseModel):
    question_text: str = Field(..., min_length=1, max_length=1000)
    question_type: str = Field(..., pattern="^(open|multiple_choice|scale|ranking|branching_gate)$")
    probing_depth: int = Field(default=3, ge=1, le=10)
    help_text: Optional[str] = Field(None, max_length=500)
    options_json: Optional[list] = None
    scale_config: Optional[dict] = None


class UpdateQuestionRequest(BaseModel):
    question_text: Optional[str] = Field(None, min_length=1, max_length=1000)
    question_type: Optional[str] = Field(None, pattern="^(open|multiple_choice|scale|ranking|branching_gate)$")
    probing_depth: Optional[int] = Field(None, ge=1, le=10)
    help_text: Optional[str] = Field(None, max_length=500)
    options_json: Optional[list] = None
    scale_config: Optional[dict] = None


class ReorderRequest(BaseModel):
    question_id: str
    new_index: int = Field(..., ge=0)


class BatchQuestionItem(BaseModel):
    """Single question for batch PUT. Full replace: all questions replaced."""

    order_index: int = Field(..., ge=0)
    question_text: str = Field(..., min_length=1, max_length=1000)
    question_type: str = Field(..., pattern="^(open|multiple_choice|scale|ranking|branching_gate)$")
    probing_depth: int = Field(default=3, ge=1, le=10)
    help_text: Optional[str] = Field(None, max_length=500)
    options_json: Optional[list] = None  # [str] or [{"text": str, "add_follow_up_branch": bool}]
    scale_config: Optional[dict] = None


class BatchPutQuestionsRequest(BaseModel):
    questions: list[BatchQuestionItem]


BRANCHING_CONDITION_TYPES = (
    "answer_contains_text",
    "selected_option_equals",
    "rating_gte",
    "rating_lte",
)


class BranchingRuleItem(BaseModel):
    condition_type: str = Field(..., pattern="^(answer_contains_text|selected_option_equals|rating_gte|rating_lte)$")
    condition_value: Union[str, int]
    logic_operator: str = Field(default="AND", pattern="^(AND|OR)$")
    target_question_id: str


class BranchingRulesRequest(BaseModel):
    rules: list[BranchingRuleItem] = Field(default_factory=list)
    default_next_question_id: Optional[str] = None
