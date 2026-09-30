"""Versioned deterministic coding handoff consumed without producer imports."""
from typing import Literal
from hashlib import sha256
from pydantic import Field,model_validator
from .semantic_review import ReviewModel

class CodingHandoff(ReviewModel):
    version:Literal[1]=1
    session_id:str=Field(min_length=1,max_length=240)
    files:dict[str,str]
    blocked_reasons:list[str]=Field(default_factory=list)
    sha256:dict[str,str]
    @model_validator(mode='after')
    def checksums(self):
        if not self.files or set(self.sha256)!=set(self.files):raise ValueError('handoff files and checksums differ')
        if any(sha256(text.encode()).hexdigest()!=self.sha256[name] for name,text in self.files.items()):raise ValueError('handoff checksum mismatch')
        return self
