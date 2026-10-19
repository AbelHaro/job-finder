from typing import Literal

from pydantic import BaseModel, Field


class JobRankingServiceResponse(BaseModel):
    score: float = Field(ge=0, le=1, description="Overall suitability before policy caps.")
    experience_fit: Literal["meets", "minor_gap", "major_gap", "senior_gap", "unspecified"] = Field(
        description="Compare mandatory role experience against documented candidate experience."
    )
    ineligible_placement: bool = Field(
        description="The role is an internship/placement or requires student status, and the candidate cannot meet that condition."
    )
    reasoning: str = Field(
        description="Briefly cite the role's actual experience/placement requirements and compare with candidate evidence."
    )

    def adjusted_score(self) -> float:
        if self.ineligible_placement:
            return 0.0
        caps = {
            "meets": 1.0,
            "minor_gap": 0.59,
            "major_gap": 0.39,
            "senior_gap": 0.29,
            "unspecified": 0.79,
        }
        return min(self.score, caps[self.experience_fit])
