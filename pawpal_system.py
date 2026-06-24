from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Task:
    name: str
    description: str
    duration_minutes: int
    priority: str          # "high" | "medium" | "low"
    category: str          # "walk" | "feeding" | "meds" | "grooming" | "enrichment" | ...
    last_completed: Optional[date] = None
    is_recurring: bool = False
    recurrence_interval_days: int = 1

    def is_due(self) -> bool: ...
    def mark_complete(self) -> None: ...
    def notify_owner(self) -> None: ...


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None: ...
    def remove_task(self, task: Task) -> None: ...
    def get_pending_tasks(self) -> list[Task]: ...


@dataclass
class ScheduledEntry:
    task: Task
    pet: Pet
    start_time: str        # "HH:MM" 24-hour string

    def get_end_time(self) -> str: ...
    def get_duration(self) -> int: ...


@dataclass
class DailyPlan:
    date: date
    entries: list[ScheduledEntry] = field(default_factory=list)
    total_duration_minutes: int = 0
    reasoning: str = ""

    def add_entry(self, entry: ScheduledEntry) -> None: ...
    def is_feasible(self, available_time: int) -> bool: ...
    def display(self) -> str: ...


@dataclass
class Scheduler:
    owner: Owner
    pets: list[Pet] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None: ...
    def modify_task(self, task: Task) -> None: ...
    def delete_task(self, task: Task) -> None: ...
    def generate_plan(self) -> DailyPlan: ...
    def sort_tasks(self) -> list[Task]: ...
    def filter_tasks(self, available_time: int) -> list[Task]: ...
    def explain_plan(self, plan: DailyPlan) -> str: ...


@dataclass
class Owner:
    name: str
    available_time_minutes: int
    pets: list[Pet] = field(default_factory=list)
    scheduler: Optional[Scheduler] = field(default=None, repr=False)

    def add_pet(self, pet: Pet) -> None: ...
    def remove_pet(self, pet: Pet) -> None: ...
    def create_schedule(self) -> DailyPlan: ...
    def set_available_time(self, minutes: int) -> None: ...
