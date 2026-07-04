from pawpal_system import Owner, Pet, Task, Scheduler

owner = Owner(name="Alex", available_time_minutes=120)

# --- Pets ---
biscuit = Pet(name="Biscuit", species="dog", breed="Golden Retriever", age=3)
whiskers = Pet(name="Whiskers", species="cat", breed="Domestic Shorthair", age=5)

# --- Biscuit's tasks ---
biscuit.add_task(Task(
    name="Morning Walk",
    description="Leash walk around the neighborhood",
    duration_minutes=30,
    priority="high",
    category="walk",
    is_recurring=True,
    recurrence_interval_days=1,
))
biscuit.add_task(Task(
    name="Grooming",
    description="Brush coat and check ears",
    duration_minutes=45,
    priority="low",
    category="grooming",
    is_recurring=True,
    recurrence_interval_days=7,
))
biscuit.add_task(Task(
    name="Breakfast",
    description="Morning kibble serving",
    duration_minutes=10,
    priority="high",
    category="feeding",
    is_recurring=True,
    recurrence_interval_days=1,
))

# --- Whiskers's tasks ---
whiskers.add_task(Task(
    name="Dinner",
    description="Evening wet food serving",
    duration_minutes=5,
    priority="high",
    category="feeding",
    is_recurring=True,
    recurrence_interval_days=1,
))
whiskers.add_task(Task(
    name="Litter Box",
    description="Scoop and refresh litter",
    duration_minutes=5,
    priority="high",
    category="grooming",
    is_recurring=True,
    recurrence_interval_days=1,
))
whiskers.add_task(Task(
    name="Play Session",
    description="Wand toy and laser pointer",
    duration_minutes=20,
    priority="medium",
    category="enrichment",
    is_recurring=True,
    recurrence_interval_days=1,
))

owner.add_pet(biscuit)
owner.add_pet(whiskers)

scheduler = Scheduler(owner=owner)
owner.scheduler = scheduler

plan = owner.create_schedule()

print("=" * 40)
print(f"  Today's Schedule for {owner.name}")
print("=" * 40)
print(plan.display())
