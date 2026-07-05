# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

Today's Schedule for Alex
========================================
Daily plan for 2026-06-23:
  08:00–08:05  Litter Box for Whiskers (5 min) [priority: high]
  08:05–08:10  Dinner for Whiskers (5 min) [priority: high]
  08:10–08:20  Breakfast for Biscuit (10 min) [priority: high]
  08:20–08:50  Morning Walk for Biscuit (30 min) [priority: high]
  08:50–09:10  Play Session for Whiskers (20 min) [priority: medium]
  09:10–09:55  Grooming for Biscuit (45 min) [priority: low]
Total: 115 min

Reasoning: Scheduled 6 task(s) using 115 of 120 available minutes. High-priority tasks placed first: Litter Box, Dinner, Breakfast, Morning Walk.

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest
python3 -m pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
==================================================== test session starts ====================================================
platform darwin -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/nishantvellanki/Documents/ai110-module2show-pawpal-starter
plugins: anyio-4.14.0
collected 35 items                                                                                                          
tests/test_pawpal.py ...................................                                                              [100%]

==================================================== 35 passed in 0.05s ===========================
Based on test results, I am fully confident in my system (5/5)

## 📐 Smarter Scheduling
Sort Tasks | By priority, then duration
Filter Tasks | By priority, based on the time allotted
Conflict Checking | Ensures tasks do not overlap
Reoccurring Tasks | Auto-rescheduling of tasks that happen on a daily, weekly basis

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. As a user, enter your name in the Owner section, as well as the time you have available in a day
2. Enter details about your pet(s), including it's name, species, breed, and age in human years. Users can enter more than one pet if they have
3. After creating a pet, give it tasks! Enter the task's name, time it will take, priority of the task, the general category, and a description of the task.
4. After entering Pets and Tasks, they will show up in a table underneath each section. Users can review an unsorted view of their schedule
5. Press Generate Schedule at the bottom of the screen to create a Schedule from the inputs in the Pets and Tasks sections. Plan will be generated in chronological order for the day, and warnings will be sent if tasks happen to go past the availability duration or there are overlapping events.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
