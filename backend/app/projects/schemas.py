"""Project API schemas."""
from typing import Optional

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
