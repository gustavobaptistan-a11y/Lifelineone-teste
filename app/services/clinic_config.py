from datetime import time
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Weekday = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class TimeWindow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: time
    end: time

    @model_validator(mode="after")
    def validate_order(self) -> "TimeWindow":
        if self.start >= self.end:
            raise ValueError("start deve ser anterior a end")
        return self


class CalendarRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default="primary", min_length=1)
    timezone: str = Field(default="America/Sao_Paulo", min_length=1)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"timezone invalido: {value}") from exc
        return value


class AppointmentRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duration_minutes: int = Field(default=30, gt=0)
    buffer_minutes: int = Field(default=10, ge=0)
    minimum_notice_hours: int = Field(default=2, ge=0)


class AvailabilityRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_options: int = Field(default=3, gt=0)
    search_days: int = Field(default=30, gt=0)
    weekly_hours: dict[Weekday, list[TimeWindow]]

    @model_validator(mode="after")
    def validate_weekdays(self) -> "AvailabilityRules":
        missing = set(Weekday.__args__) - set(self.weekly_hours)
        if missing:
            raise ValueError(f"dias ausentes na configuracao: {sorted(missing)}")
        return self


class ConflictRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ignore_statuses: list[str] = Field(default_factory=lambda: ["cancelled", "canceled"])
    overlap_is_conflict: bool = True
    search_next_available: bool = True
    prevent_duplicate_event: bool = True


class ExceptionRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    holidays: list[dict[str, Any]] = Field(default_factory=list)
    vacations: list[dict[str, Any]] = Field(default_factory=list)
    blocked_periods: list[dict[str, Any]] = Field(default_factory=list)


class ClinicScheduleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    calendar: CalendarRules
    appointment: AppointmentRules
    availability: AvailabilityRules
    conflicts: ConflictRules
    exceptions: ExceptionRules


def default_config_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "clinic.yaml"


def load_clinic_config(path: str | Path | None = None) -> ClinicScheduleConfig:
    config_path = Path(path) if path else default_config_path()
    with config_path.open("r", encoding="utf-8") as config_file:
        raw_config = yaml.safe_load(config_file) or {}
    return ClinicScheduleConfig.model_validate(raw_config)


clinic_schedule_config = load_clinic_config()
