"""Editable exploration tasks using the existing bounded mathematical runners."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat
from app.math_tools.numerical_lab import LinearTask
from app.math_tools.root_expression import RootExpression
from pydantic import field_validator


class GS(LinearTask):
    method: Literal["gauss_seidel"] = "gauss_seidel"


class NewtonTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    domain: Literal["root_finding"] = "root_finding"
    method: Literal["newton"] = "newton"
    function: str = Field(min_length=1, max_length=200)
    initial_value: FiniteFloat = Field(ge=-1e6, le=1e6)
    tolerance: FiniteFloat = Field(default=1e-6, ge=1e-12, le=0.01)
    limit: int = Field(default=20, ge=1, le=100)

    @field_validator("function")
    @classmethod
    def expression(cls, value):
        RootExpression(value)
        return value


ExplorationTask = Annotated[GS | NewtonTask, Field(discriminator="domain")]
