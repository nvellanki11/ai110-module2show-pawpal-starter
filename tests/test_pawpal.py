from datetime import date
from pawpal_system import Task, Pet


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
