"""Editable exploration tasks using the existing bounded mathematical runners."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat
from app.math_tools.numerical_lab import LinearTask, IntegrationTask, Scalar
from app.math_tools.root_expression import RootExpression
from pydantic import field_validator, model_validator


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


class QuadratureTask(IntegrationTask):
    expression: str = Field(min_length=1, max_length=200)
    left: Scalar
    right: Scalar
    @field_validator("expression")
    @classmethod
    def expression_valid(cls, value):
        RootExpression(value)
        return value


ExplorationTask = Annotated[GS | NewtonTask | QuadratureTask, Field(discriminator="domain")]
ShortText = Annotated[str, Field(min_length=1, max_length=500)]


class ExperimentPlan(BaseModel):
    """A proposal, with domain-shaped tasks. It does not authorize execution."""
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["experiment-plan-v1"] = "experiment-plan-v1"
    claim_to_test: str = Field(min_length=1, max_length=2000)
    known_conditions: list[ShortText] = Field(max_length=8)
    question_to_test: str = Field(min_length=1, max_length=300)
    changed_parameter: Literal["task_parameters"] = "task_parameters"
    tasks: list[ExplorationTask] = Field(min_length=1, max_length=2)
    varying_factors: list[ShortText] = Field(min_length=1, max_length=8)
    fixed_factors: list[ShortText] = Field(min_length=1, max_length=8)
    observable: str = Field(min_length=1, max_length=200)
    mathematical_reason: str = Field(min_length=1, max_length=600)
    tool_limitations: list[ShortText] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def controlled_comparison(self):
        first = self.tasks[0].model_dump()
        if any(t.domain != self.tasks[0].domain for t in self.tasks):
            raise ValueError("一份对照计划须使用同一领域的任务")
        names = set(first) - {"domain"}
        varying, fixed = set(self.varying_factors), set(self.fixed_factors)
        if not (varying | fixed) <= names or varying & fixed:
            raise ValueError("因素须使用任务字段名；变化与保持因素不能重叠")
        if all(t.method == "adaptive_simpson" for t in self.tasks) and "intervals" in varying:
            raise ValueError("自适应Simpson不使用初始分段数控制求积，请比较容差或预算")
        if len(self.tasks) == 2:
            second = self.tasks[1].model_dump()
            changes = {k for k in names if first[k] != second[k]}
            if not changes or not changes <= varying or changes & fixed:
                raise ValueError("对照任务的实际变化须与声明因素一致")
        return self
