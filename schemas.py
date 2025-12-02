from typing import List, Optional
from pydantic import BaseModel, validator
from pydantic.config import ConfigDict


class PredictionRequest(BaseModel):
    features: List[float]

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    @validator("features")
    def check_features_length(cls, v):
        """Проверка длины массива признаков."""
        if len(v) == 0:
            raise ValueError("Массив признаков не может быть пустым")
        return v


class PredictionResponse(BaseModel):
    prediction: float
    probabilities: Optional[List[float]] = None

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )


class User(BaseModel):
    username: str
    phone: str
    email: str
    role: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
