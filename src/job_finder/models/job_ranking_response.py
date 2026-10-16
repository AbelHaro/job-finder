from pydantic import BaseModel


class JobRankingServiceResponse(BaseModel):
    score: float
