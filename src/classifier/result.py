from pydantic import BaseModel, Field

class NSFWClassifierResult(BaseModel):
    nsfw: bool = Field(..., description="Whether or not the image is NSFW")
    max_score: float = Field(..., description="The maximum score of the image")
    results: list[dict] = Field(..., description="The results of the image")
