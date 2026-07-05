import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

st.divider()

# --- Owner ---
st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")
available_time = st.number_input("Available time (minutes)", min_value=0, value=120)

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, available_time_minutes=int(available_time))
owner: Owner = st.session_state.owner
owner.name = owner_name
owner.available_time_minutes = int(available_time)

# --- Pets ---
st.divider()
st.subheader("Pets")

with st.form("add_pet_form", clear_on_submit=True):
    pet_col1, pet_col2, pet_col3, pet_col4 = st.columns(4)
    with pet_col1:
        new_pet_name = st.text_input("Pet name")
    with pet_col2:
        new_species = st.selectbox("Species", ["dog", "cat", "other"])
    with pet_col3:
        new_breed = st.text_input("Breed")
    with pet_col4:
        new_age = st.number_input("Age (years)", min_value=0, max_value=30, value=0)
    add_pet_submitted = st.form_submit_button("Add pet")

if add_pet_submitted:
    if new_pet_name:
        owner.add_pet(Pet(name=new_pet_name, species=new_species, breed=new_breed, age=int(new_age)))
        st.toast(f"Added {new_pet_name}!", icon="🐾")
        st.rerun()
    else:
        st.warning("Enter a pet name before adding.")

if owner.pets:
    st.table([
        {
            "name": p.name,
            "species": p.species,
            "breed": p.breed,
            "age": p.age,
            "tasks": len(p.tasks),
        }
        for p in owner.pets
    ])
else:
    st.info("No pets yet. Add one above.")

# --- Tasks ---
st.divider()
st.subheader("Tasks")

if not owner.pets:
    st.info("Add a pet before creating tasks.")
else:
    pet_index = st.selectbox(
        "Pet", options=list(range(len(owner.pets))), format_func=lambda i: owner.pets[i].name
    )
    pet: Pet = owner.pets[pet_index]

    with st.form("add_task_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

        col4, col5 = st.columns(2)
        with col4:
            category = st.selectbox("Category", ["walk", "feeding", "meds", "grooming", "enrichment", "other"])
        with col5:
            description = st.text_input("Description", value="")

        add_task_submitted = st.form_submit_button("Add task")

    if add_task_submitted:
        if task_title:
            pet.add_task(Task(
                name=task_title,
                description=description,
                duration_minutes=int(duration),
                priority=priority,
                category=category,
            ))
            st.toast(f"Added task '{task_title}' for {pet.name}!", icon="🐾")
            st.rerun()
        else:
            st.warning("Enter a task title before adding.")

    if pet.tasks:
        display_scheduler = Scheduler(owner=owner, tasks=list(pet.tasks))
        sorted_tasks = display_scheduler.sort_tasks()
        pending_tasks = pet.get_pending_tasks()
        fitting_task_ids = {id(t) for t in display_scheduler.filter_tasks(owner.available_time_minutes)}

        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            status_filter = st.selectbox("Filter by status", ["All", "Pending", "Completed"])
        with filter_col2:
            pet_name_filter = st.text_input("Filter by pet name", value="")

        filtered_tasks = sorted_tasks
        if status_filter == "Pending":
            filtered_tasks = [t for t in filtered_tasks if t.is_due()]
        elif status_filter == "Completed":
            filtered_tasks = [t for t in filtered_tasks if not t.is_due()]
        if pet_name_filter:
            if pet_name_filter.lower() not in pet.name.lower():
                filtered_tasks = []

        if filtered_tasks:
            st.write(f"Tasks for {pet.name}, sorted by priority then duration:")
            st.table([
                {
                    "name": t.name,
                    "duration (min)": t.duration_minutes,
                    "priority": t.priority,
                    "category": t.category,
                    "status": "Pending" if t.is_due() else "Completed",
                    "fits today": "✅ Yes" if id(t) in fitting_task_ids else "⏳ No",
                }
                for t in filtered_tasks
            ])

            pending_minutes = sum(t.duration_minutes for t in pending_tasks)
            if pending_minutes > owner.available_time_minutes:
                overflow_names = [t.name for t in pending_tasks if id(t) not in fitting_task_ids]
                st.warning(
                    f"Soft conflict: pending tasks need {pending_minutes} min, which is "
                    f"{pending_minutes - owner.available_time_minutes} min over your "
                    f"{owner.available_time_minutes}-min budget. Likely to be skipped: "
                    f"{', '.join(overflow_names)}."
                )
            else:
                st.success("All pending tasks fit within your available time today.")
        else:
            st.info("No tasks match the selected filters.")
    else:
        st.info(f"No tasks yet for {pet.name}. Add one above.")

# --- Schedule ---
st.divider()
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not any(p.tasks for p in owner.pets):
        st.warning("Add at least one task before generating a schedule.")
    else:
        owner.scheduler = Scheduler(owner=owner)
        plan = owner.create_schedule()
        st.success("Schedule generated!")
        st.text(plan.display())

        conflict_warnings = owner.scheduler.get_conflict_warnings(plan)
        if conflict_warnings:
            for warning in conflict_warnings:
                st.warning(warning)
        else:
            st.success("No conflicts — your schedule is clash-free.")
