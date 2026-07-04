import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

st.divider()

# --- Owner ---
st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")
available_time = st.number_input("Available time (minutes)", min_value=0, value=120)

if (
    "owner" not in st.session_state
    or st.session_state.owner.name != owner_name
    or st.session_state.owner.available_time_minutes != available_time
):
    st.session_state.owner = Owner(name=owner_name, available_time_minutes=int(available_time))

# --- Pet ---
st.subheader("Pet")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
breed = st.text_input("Breed", value="Mixed")
age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)

if (
    "pet" not in st.session_state
    or st.session_state.pet.name != pet_name
    or st.session_state.pet.species != species
    or st.session_state.pet.breed != breed
    or st.session_state.pet.age != age
):
    st.session_state.pet = Pet(name=pet_name, species=species, breed=breed, age=int(age))

# Keep owner's pet list in sync with the current pet
owner: Owner = st.session_state.owner
pet: Pet = st.session_state.pet
if pet not in owner.pets:
    owner.pets.clear()
    owner.add_pet(pet)

# --- Tasks ---
st.divider()
st.subheader("Tasks")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

col4, col5 = st.columns(2)
with col4:
    category = st.selectbox("Category", ["walk", "feeding", "meds", "grooming", "enrichment", "other"])
with col5:
    description = st.text_input("Description", value="")

if st.button("Add task"):
    pet.add_task(Task(
        name=task_title,
        description=description,
        duration_minutes=int(duration),
        priority=priority,
        category=category,
    ))

if pet.tasks:
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        status_filter = st.selectbox("Filter by status", ["All", "Pending", "Completed"])
    with filter_col2:
        pet_name_filter = st.text_input("Filter by pet name", value="")

    filtered_tasks = pet.tasks
    if status_filter == "Pending":
        filtered_tasks = [t for t in filtered_tasks if t.is_due()]
    elif status_filter == "Completed":
        filtered_tasks = [t for t in filtered_tasks if not t.is_due()]
    if pet_name_filter:
        if pet_name_filter.lower() not in pet.name.lower():
            filtered_tasks = []

    if filtered_tasks:
        st.write(f"Tasks for {pet.name}:")
        st.table([
            {
                "name": t.name,
                "duration (min)": t.duration_minutes,
                "priority": t.priority,
                "category": t.category,
                "status": "Pending" if t.is_due() else "Completed",
            }
            for t in filtered_tasks
        ])
    else:
        st.info("No tasks match the selected filters.")
else:
    st.info("No tasks yet. Add one above.")

# --- Schedule ---
st.divider()
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not pet.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        owner.scheduler = Scheduler(owner=owner)
        plan = owner.create_schedule()
        st.success("Schedule generated!")
        st.text(plan.display())

        for warning in owner.scheduler.get_conflict_warnings(plan):
            st.warning(warning)
