from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _time_to_minutes(time_str: str) -> int:
    """Convert an "HH:MM" string to minutes since midnight."""
    h, m = map(int, time_str.split(":"))
    return h * 60 + m


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

    def is_due(self) -> bool:
        """Return True if this task has never been done or its recurrence interval has elapsed."""
        if self.last_completed is None:
            return True
        if not self.is_recurring:
            return False
        return (date.today() - self.last_completed).days >= self.recurrence_interval_days

    def mark_complete(self) -> None:
        """Stamp last_completed with today's date."""
        self.last_completed = date.today()


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet's task list."""
        self.tasks.remove(task)

    def get_pending_tasks(self) -> list[Task]:
        """Return all tasks that are currently due."""
        return [t for t in self.tasks if t.is_due()]


@dataclass
class ScheduledEntry:
    task: Task
    pet: Pet
    start_time: str        # "HH:MM" 24-hour string

    def get_end_time(self) -> str:
        """Compute the HH:MM end time from start_time plus task duration."""
        total = _time_to_minutes(self.start_time) + self.task.duration_minutes
        return f"{total // 60:02d}:{total % 60:02d}"


@dataclass
class DailyPlan:
    date: date
    entries: list[ScheduledEntry] = field(default_factory=list)
    total_duration_minutes: int = 0
    reasoning: str = ""

    def add_entry(self, entry: ScheduledEntry) -> None:
        """Append a scheduled entry and update the running total duration."""
        self.entries.append(entry)
        self.total_duration_minutes += entry.task.duration_minutes

    def is_feasible(self, available_time: int) -> bool:
        """Return True if the plan's total duration fits within available_time."""
        return self.total_duration_minutes <= available_time

    def display(self) -> str:
        """Format the plan as a human-readable schedule string."""
        if not self.entries:
            return "No tasks scheduled for today."
        lines = [f"Daily plan for {self.date}:"]
        for entry in self.entries:
            lines.append(
                f"  {entry.start_time}–{entry.get_end_time()}  "
                f"{entry.task.name} for {entry.pet.name} "
                f"({entry.task.duration_minutes} min) [priority: {entry.task.priority}]"
            )
        lines.append(f"Total: {self.total_duration_minutes} min")
        if self.reasoning:
            lines.append(f"\nReasoning: {self.reasoning}")
        return "\n".join(lines)


@dataclass
class Scheduler:
    owner: Owner
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to the scheduler's managed task list."""
        self.tasks.append(task)

    def modify_task(self, task: Task) -> None:
        """Replace the existing task that shares the same name with the updated version."""
        for i, t in enumerate(self.tasks):
            if t.name == task.name:
                self.tasks[i] = task
                return
        raise ValueError(f"Task '{task.name}' not found.")

    def delete_task(self, task: Task) -> None:
        """Remove a task from the scheduler's managed task list."""
        self.tasks.remove(task)

    def complete_task(self, task: Task) -> Optional[Task]:
        """Mark a task complete; if it recurs daily or weekly, add a new instance for the next occurrence."""
        task.mark_complete()
        if not task.is_recurring or task.recurrence_interval_days not in (1, 7):
            return None

        owning_pet = next((pet for pet in self.owner.pets if task in pet.tasks), None)
        if owning_pet is None:
            return None

        next_task = Task(
            name=task.name,
            description=task.description,
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            category=task.category,
            is_recurring=task.is_recurring,
            recurrence_interval_days=task.recurrence_interval_days,
        )
        owning_pet.add_task(next_task)
        return next_task

    def find_conflicts(self, plan: DailyPlan) -> list[tuple[ScheduledEntry, ScheduledEntry]]:
        """Return pairs of entries in the plan whose time ranges overlap, regardless of pet."""
        conflicts = []
        for i, entry_a in enumerate(plan.entries):
            start_a = _time_to_minutes(entry_a.start_time)
            end_a = start_a + entry_a.task.duration_minutes
            for entry_b in plan.entries[i + 1:]:
                start_b = _time_to_minutes(entry_b.start_time)
                end_b = start_b + entry_b.task.duration_minutes
                if start_a < end_b and start_b < end_a:
                    conflicts.append((entry_a, entry_b))
        return conflicts

    def has_conflicts(self, plan: DailyPlan) -> bool:
        """Return True if any two entries in the plan overlap in time."""
        return bool(self.find_conflicts(plan))

    def get_conflict_warnings(self, plan: DailyPlan) -> list[str]:
        """Return a human-readable warning message for each pair of entries scheduled at the same time."""
        return [
            f"Warning: '{entry_a.task.name}' for {entry_a.pet.name} "
            f"({entry_a.start_time}-{entry_a.get_end_time()}) overlaps with "
            f"'{entry_b.task.name}' for {entry_b.pet.name} "
            f"({entry_b.start_time}-{entry_b.get_end_time()})."
            for entry_a, entry_b in self.find_conflicts(plan)
        ]

    def sort_tasks(self) -> list[Task]:
        """Return tasks sorted by priority (high→low) then shortest duration first."""
        return sorted(
            self.tasks,
            key=lambda t: (_PRIORITY_ORDER.get(t.priority, 3), t.duration_minutes),
        )

    def filter_tasks(self, available_time: int) -> list[Task]:
        """Return the priority-sorted subset of tasks that fits within available_time."""
        result, time_used = [], 0
        for task in self.sort_tasks():
            if time_used + task.duration_minutes <= available_time:
                result.append(task)
                time_used += task.duration_minutes
        return result

    def generate_plan(self) -> DailyPlan:
        """Build today's DailyPlan by collecting, sorting, and greedily scheduling due tasks."""
        plan = DailyPlan(date=date.today())

        # Collect (task, pet) pairs for every due task across all pets
        candidates: list[tuple[Task, Pet]] = [
            (task, pet)
            for pet in self.owner.pets
            for task in pet.get_pending_tasks()
        ]

        # High priority first; break ties by shortest duration (fits more tasks in)
        candidates.sort(
            key=lambda tp: (_PRIORITY_ORDER.get(tp[0].priority, 3), tp[0].duration_minutes)
        )

        # Greedily assign time slots starting at 08:00; skip tasks that don't fit
        # (continue rather than break so a short low-priority task can fill remaining time)
        cursor = 8 * 60
        for task, pet in candidates:
            if plan.total_duration_minutes + task.duration_minutes > self.owner.available_time_minutes:
                continue
            start = f"{cursor // 60:02d}:{cursor % 60:02d}"
            plan.add_entry(ScheduledEntry(task=task, pet=pet, start_time=start))
            cursor += task.duration_minutes

        plan.reasoning = self.explain_plan(plan)
        return plan

    def explain_plan(self, plan: DailyPlan) -> str:
        """Summarize why tasks were included or skipped in the given plan."""
        if not plan.entries:
            return "No tasks are due today."

        lines: list[str] = [
            f"Scheduled {len(plan.entries)} task(s) using "
            f"{plan.total_duration_minutes} of {self.owner.available_time_minutes} available minutes."
        ]

        high_priority_names = [e.task.name for e in plan.entries if e.task.priority == "high"]
        if high_priority_names:
            lines.append(f"High-priority tasks placed first: {', '.join(high_priority_names)}.")

        all_due = sum(len(p.get_pending_tasks()) for p in self.owner.pets)
        skipped = all_due - len(plan.entries)
        if skipped > 0:
            lines.append(f"{skipped} task(s) skipped: insufficient time remaining.")

        return " ".join(lines)


@dataclass
class Owner:
    name: str
    available_time_minutes: int
    pets: list[Pet] = field(default_factory=list)
    scheduler: Optional[Scheduler] = field(default=None, repr=False)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pet list."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner's pet list."""
        self.pets.remove(pet)

    def create_schedule(self) -> DailyPlan:
        """Delegate to the assigned scheduler to generate today's plan."""
        if self.scheduler is None:
            raise ValueError("No scheduler assigned to this owner.")
        return self.scheduler.generate_plan()
