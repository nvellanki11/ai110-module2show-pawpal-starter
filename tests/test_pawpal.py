from datetime import date, timedelta

import pytest

from pawpal_system import Task, Pet, Owner, Scheduler, DailyPlan, ScheduledEntry


def make_task(**kwargs) -> Task:
    defaults = dict(
        name="Test task",
        description="desc",
        duration_minutes=10,
        priority="medium",
        category="walk",
    )
    return Task(**{**defaults, **kwargs})


def test_mark_complete_sets_last_completed_to_today():
    task = make_task()
    assert task.last_completed is None
    task.mark_complete()
    assert task.last_completed == date.today()


def test_mark_complete_makes_non_recurring_task_not_due():
    task = make_task(is_recurring=False)
    assert task.is_due()
    task.mark_complete()
    assert not task.is_due()


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Biscuit", species="dog", breed="Labrador", age=2)
    assert len(pet.tasks) == 0
    pet.add_task(make_task(name="Walk"))
    assert len(pet.tasks) == 1
    pet.add_task(make_task(name="Feed"))
    assert len(pet.tasks) == 2


def make_owner_with_task(**task_kwargs) -> tuple[Owner, Pet, Task]:
    owner = Owner(name="Jordan", available_time_minutes=120)
    pet = Pet(name="Biscuit", species="dog", breed="Labrador", age=2)
    task = make_task(**task_kwargs)
    pet.add_task(task)
    owner.add_pet(pet)
    return owner, pet, task


def test_complete_task_marks_task_complete():
    owner, pet, task = make_owner_with_task()
    scheduler = Scheduler(owner=owner)
    scheduler.complete_task(task)
    assert task.last_completed == date.today()


def test_complete_task_creates_next_occurrence_for_daily_task():
    owner, pet, task = make_owner_with_task(is_recurring=True, recurrence_interval_days=1)
    scheduler = Scheduler(owner=owner)
    next_task = scheduler.complete_task(task)
    assert next_task is not None
    assert next_task is not task
    assert next_task.last_completed is None
    assert next_task.name == task.name
    assert len(pet.tasks) == 2


def test_complete_task_creates_next_occurrence_for_weekly_task():
    owner, pet, task = make_owner_with_task(is_recurring=True, recurrence_interval_days=7)
    scheduler = Scheduler(owner=owner)
    next_task = scheduler.complete_task(task)
    assert next_task is not None
    assert len(pet.tasks) == 2


def test_complete_task_does_not_create_next_occurrence_for_non_recurring_task():
    owner, pet, task = make_owner_with_task(is_recurring=False)
    scheduler = Scheduler(owner=owner)
    next_task = scheduler.complete_task(task)
    assert next_task is None
    assert len(pet.tasks) == 1


def test_complete_task_does_not_create_next_occurrence_for_other_intervals():
    owner, pet, task = make_owner_with_task(is_recurring=True, recurrence_interval_days=3)
    scheduler = Scheduler(owner=owner)
    next_task = scheduler.complete_task(task)
    assert next_task is None
    assert len(pet.tasks) == 1


def test_find_conflicts_detects_overlap_for_same_pet():
    owner = Owner(name="Jordan", available_time_minutes=120)
    pet = Pet(name="Biscuit", species="dog", breed="Labrador", age=2)
    owner.add_pet(pet)
    plan = DailyPlan(date=date.today())
    entry_a = ScheduledEntry(task=make_task(name="Walk", duration_minutes=30), pet=pet, start_time="08:00")
    entry_b = ScheduledEntry(task=make_task(name="Feed", duration_minutes=30), pet=pet, start_time="08:15")
    plan.add_entry(entry_a)
    plan.add_entry(entry_b)

    scheduler = Scheduler(owner=owner)
    conflicts = scheduler.find_conflicts(plan)
    assert conflicts == [(entry_a, entry_b)]
    assert scheduler.has_conflicts(plan)


def test_find_conflicts_detects_overlap_across_different_pets():
    owner = Owner(name="Jordan", available_time_minutes=120)
    pet_a = Pet(name="Biscuit", species="dog", breed="Labrador", age=2)
    pet_b = Pet(name="Mochi", species="cat", breed="Mixed", age=3)
    owner.add_pet(pet_a)
    owner.add_pet(pet_b)
    plan = DailyPlan(date=date.today())
    entry_a = ScheduledEntry(task=make_task(name="Walk", duration_minutes=30), pet=pet_a, start_time="08:00")
    entry_b = ScheduledEntry(task=make_task(name="Groom", duration_minutes=30), pet=pet_b, start_time="08:15")
    plan.add_entry(entry_a)
    plan.add_entry(entry_b)

    scheduler = Scheduler(owner=owner)
    conflicts = scheduler.find_conflicts(plan)
    assert conflicts == [(entry_a, entry_b)]


def test_find_conflicts_returns_empty_for_back_to_back_entries():
    owner = Owner(name="Jordan", available_time_minutes=120)
    pet = Pet(name="Biscuit", species="dog", breed="Labrador", age=2)
    owner.add_pet(pet)
    plan = DailyPlan(date=date.today())
    plan.add_entry(ScheduledEntry(task=make_task(name="Walk", duration_minutes=30), pet=pet, start_time="08:00"))
    plan.add_entry(ScheduledEntry(task=make_task(name="Feed", duration_minutes=30), pet=pet, start_time="08:30"))

    scheduler = Scheduler(owner=owner)
    assert scheduler.find_conflicts(plan) == []
    assert not scheduler.has_conflicts(plan)


def test_get_conflict_warnings_describes_each_overlap():
    owner = Owner(name="Jordan", available_time_minutes=120)
    pet = Pet(name="Biscuit", species="dog", breed="Labrador", age=2)
    owner.add_pet(pet)
    plan = DailyPlan(date=date.today())
    plan.add_entry(ScheduledEntry(task=make_task(name="Walk", duration_minutes=30), pet=pet, start_time="08:00"))
    plan.add_entry(ScheduledEntry(task=make_task(name="Feed", duration_minutes=30), pet=pet, start_time="08:15"))

    scheduler = Scheduler(owner=owner)
    warnings = scheduler.get_conflict_warnings(plan)
    assert len(warnings) == 1
    assert "Walk" in warnings[0]
    assert "Feed" in warnings[0]
    assert "Biscuit" in warnings[0]


def test_get_conflict_warnings_empty_when_no_overlap():
    owner = Owner(name="Jordan", available_time_minutes=120)
    pet = Pet(name="Biscuit", species="dog", breed="Labrador", age=2)
    owner.add_pet(pet)
    plan = DailyPlan(date=date.today())
    plan.add_entry(ScheduledEntry(task=make_task(name="Walk", duration_minutes=30), pet=pet, start_time="08:00"))
    plan.add_entry(ScheduledEntry(task=make_task(name="Feed", duration_minutes=30), pet=pet, start_time="08:30"))

    scheduler = Scheduler(owner=owner)
    assert scheduler.get_conflict_warnings(plan) == []


# --- Sorting / tie-breaking edge cases ---

def test_sort_tasks_stable_for_equal_priority_and_duration():
    scheduler = Scheduler(owner=Owner(name="Jordan", available_time_minutes=120))
    task_a = make_task(name="A", priority="medium", duration_minutes=10)
    task_b = make_task(name="B", priority="medium", duration_minutes=10)
    scheduler.add_task(task_a)
    scheduler.add_task(task_b)

    assert scheduler.sort_tasks() == [task_a, task_b]


def test_sort_tasks_unknown_priority_sorts_last():
    scheduler = Scheduler(owner=Owner(name="Jordan", available_time_minutes=120))
    task_unknown = make_task(name="Unknown", priority="urgent", duration_minutes=1)
    task_high = make_task(name="High", priority="high", duration_minutes=100)
    scheduler.add_task(task_unknown)
    scheduler.add_task(task_high)

    assert scheduler.sort_tasks() == [task_high, task_unknown]


def test_sort_tasks_empty_list_returns_empty():
    scheduler = Scheduler(owner=Owner(name="Jordan", available_time_minutes=120))
    assert scheduler.sort_tasks() == []


def test_filter_tasks_empty_list_returns_empty():
    scheduler = Scheduler(owner=Owner(name="Jordan", available_time_minutes=120))
    assert scheduler.filter_tasks(120) == []


# --- Recurring task edge cases ---

def test_is_due_true_when_elapsed_days_equals_interval():
    task = make_task(is_recurring=True, recurrence_interval_days=7)
    task.last_completed = date.today() - timedelta(days=7)
    assert task.is_due()


def test_is_due_false_when_elapsed_days_less_than_interval():
    task = make_task(is_recurring=True, recurrence_interval_days=7)
    task.last_completed = date.today() - timedelta(days=6)
    assert not task.is_due()


def test_is_due_true_immediately_for_zero_interval_recurring_task():
    task = make_task(is_recurring=True, recurrence_interval_days=0)
    task.mark_complete()
    assert task.is_due()


def test_complete_task_original_task_becomes_due_again_after_other_interval():
    owner, pet, task = make_owner_with_task(is_recurring=True, recurrence_interval_days=3)
    scheduler = Scheduler(owner=owner)
    next_task = scheduler.complete_task(task)
    assert next_task is None
    assert len(pet.tasks) == 1

    task.last_completed = date.today() - timedelta(days=3)
    assert task.is_due()


def test_complete_task_returns_none_when_task_not_owned_by_any_pet():
    owner = Owner(name="Jordan", available_time_minutes=120)
    task = make_task(is_recurring=True, recurrence_interval_days=1)
    scheduler = Scheduler(owner=owner)

    next_task = scheduler.complete_task(task)
    assert next_task is None
    assert task.last_completed == date.today()


# --- Scheduling edge cases ---

def test_generate_plan_skips_pet_with_no_tasks():
    owner = Owner(name="Jordan", available_time_minutes=120)
    empty_pet = Pet(name="Empty", species="dog", breed="Mixed", age=1)
    pet_with_task = Pet(name="Biscuit", species="dog", breed="Labrador", age=2)
    pet_with_task.add_task(make_task(name="Walk"))
    owner.add_pet(empty_pet)
    owner.add_pet(pet_with_task)
    owner.scheduler = Scheduler(owner=owner)

    plan = owner.create_schedule()
    assert len(plan.entries) == 1
    assert plan.entries[0].pet is pet_with_task


def test_generate_plan_empty_when_owner_has_no_pets():
    owner = Owner(name="Jordan", available_time_minutes=120)
    owner.scheduler = Scheduler(owner=owner)

    plan = owner.create_schedule()
    assert plan.entries == []
    assert plan.display() == "No tasks scheduled for today."


def test_generate_plan_empty_when_available_time_zero():
    owner = Owner(name="Jordan", available_time_minutes=0)
    pet = Pet(name="Biscuit", species="dog", breed="Labrador", age=2)
    pet.add_task(make_task(duration_minutes=10))
    owner.add_pet(pet)
    owner.scheduler = Scheduler(owner=owner)

    plan = owner.create_schedule()
    assert plan.entries == []


def test_generate_plan_continues_past_oversized_task_to_schedule_smaller_one():
    owner = Owner(name="Jordan", available_time_minutes=20)
    pet = Pet(name="Biscuit", species="dog", breed="Labrador", age=2)
    big_task = make_task(name="Big", duration_minutes=30, priority="high")
    small_task = make_task(name="Small", duration_minutes=10, priority="low")
    pet.add_task(big_task)
    pet.add_task(small_task)
    owner.add_pet(pet)
    owner.scheduler = Scheduler(owner=owner)

    plan = owner.create_schedule()
    assert len(plan.entries) == 1
    assert plan.entries[0].task is small_task


# --- Conflict detection edge cases ---

def test_find_conflicts_detects_full_overlap_at_same_start_time():
    owner = Owner(name="Jordan", available_time_minutes=120)
    pet = Pet(name="Biscuit", species="dog", breed="Labrador", age=2)
    owner.add_pet(pet)
    plan = DailyPlan(date=date.today())
    entry_a = ScheduledEntry(task=make_task(name="Walk", duration_minutes=30), pet=pet, start_time="08:00")
    entry_b = ScheduledEntry(task=make_task(name="Feed", duration_minutes=30), pet=pet, start_time="08:00")
    plan.add_entry(entry_a)
    plan.add_entry(entry_b)

    scheduler = Scheduler(owner=owner)
    assert scheduler.find_conflicts(plan) == [(entry_a, entry_b)]


def test_find_conflicts_zero_duration_task_does_not_conflict_with_adjacent_task():
    owner = Owner(name="Jordan", available_time_minutes=120)
    pet = Pet(name="Biscuit", species="dog", breed="Labrador", age=2)
    owner.add_pet(pet)
    plan = DailyPlan(date=date.today())
    plan.add_entry(ScheduledEntry(task=make_task(name="Walk", duration_minutes=30), pet=pet, start_time="08:00"))
    plan.add_entry(ScheduledEntry(task=make_task(name="Instant", duration_minutes=0), pet=pet, start_time="08:30"))

    scheduler = Scheduler(owner=owner)
    assert scheduler.find_conflicts(plan) == []


def test_find_conflicts_returns_empty_for_single_entry():
    owner = Owner(name="Jordan", available_time_minutes=120)
    pet = Pet(name="Biscuit", species="dog", breed="Labrador", age=2)
    owner.add_pet(pet)
    plan = DailyPlan(date=date.today())
    plan.add_entry(ScheduledEntry(task=make_task(name="Walk", duration_minutes=30), pet=pet, start_time="08:00"))

    scheduler = Scheduler(owner=owner)
    assert scheduler.find_conflicts(plan) == []


def test_find_conflicts_returns_empty_for_empty_plan():
    owner = Owner(name="Jordan", available_time_minutes=120)
    plan = DailyPlan(date=date.today())
    scheduler = Scheduler(owner=owner)
    assert scheduler.find_conflicts(plan) == []


def test_find_conflicts_detects_all_pairs_for_three_overlapping_entries():
    owner = Owner(name="Jordan", available_time_minutes=120)
    pet = Pet(name="Biscuit", species="dog", breed="Labrador", age=2)
    owner.add_pet(pet)
    plan = DailyPlan(date=date.today())
    entry_a = ScheduledEntry(task=make_task(name="A", duration_minutes=30), pet=pet, start_time="08:00")
    entry_b = ScheduledEntry(task=make_task(name="B", duration_minutes=30), pet=pet, start_time="08:15")
    entry_c = ScheduledEntry(task=make_task(name="C", duration_minutes=30), pet=pet, start_time="08:20")
    plan.add_entry(entry_a)
    plan.add_entry(entry_b)
    plan.add_entry(entry_c)

    scheduler = Scheduler(owner=owner)
    conflicts = scheduler.find_conflicts(plan)
    assert len(conflicts) == 3
    assert (entry_a, entry_b) in conflicts
    assert (entry_a, entry_c) in conflicts
    assert (entry_b, entry_c) in conflicts


# --- Error path edge cases ---

def test_modify_task_raises_when_task_not_found():
    scheduler = Scheduler(owner=Owner(name="Jordan", available_time_minutes=120))
    with pytest.raises(ValueError):
        scheduler.modify_task(make_task(name="Ghost"))


def test_delete_task_raises_when_task_not_in_list():
    scheduler = Scheduler(owner=Owner(name="Jordan", available_time_minutes=120))
    with pytest.raises(ValueError):
        scheduler.delete_task(make_task())


def test_remove_pet_raises_when_pet_not_in_list():
    owner = Owner(name="Jordan", available_time_minutes=120)
    ghost_pet = Pet(name="Ghost", species="dog", breed="Mixed", age=1)
    with pytest.raises(ValueError):
        owner.remove_pet(ghost_pet)


def test_remove_task_raises_when_task_not_in_pet():
    pet = Pet(name="Biscuit", species="dog", breed="Labrador", age=2)
    with pytest.raises(ValueError):
        pet.remove_task(make_task())
