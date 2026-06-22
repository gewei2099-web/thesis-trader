from pydantic import BaseModel, Field

from .enums import ActionType


class DecisionResult(BaseModel):
    symbol: str
    name: str = ""
    action: ActionType
    reduce_pct: int = Field(default=0, ge=0, le=100)
    triggers: list[str] = Field(default_factory=list)
    rationale: str = ""
    priority: int = Field(default=0, description="越高越优先")
