from pydantic import BaseModel
from typing import List, Optional


class NodeResult(BaseModel):
    html: str
    target: List[str]
    failureSummary: Optional[str] = None


class Violation(BaseModel):    
    id: str
    description: str
    nodes: List[NodeResult]
    impact: Optional[str] = None

class WCAGCheckResponse(BaseModel):
    violations: List[Violation]