from datetime import date
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
