# AI Usage Disclosure Document

This document fulfills the AI disclosure requirement of the assignment, detailing how AI assistance was leveraged during the conception, implementation, and verification of the **AI-Assisted Box Selection System**.

---

## 1. AI Tool(s) Used
- **Primary AI Tool**: Google Antigravity Coding Assistant (powered by the Gemini 3.8 Flash High model).
- **Environment**: Antigravity Pair-Programming Agent integrated directly into the workspace terminal and file system.
- **Python / Framework Environment**: Python 3.12.0, Django 5.2.18, Django REST Framework 3.18.0.

---

## 2. Prompts Given

The following core prompts and instructions guided the AI assistance:

1. **Initial Requirement Ingestion & Verification**:
   > *"Read all assignment content from the assignment docx in Downloads and implement the full project fulfilling all requirements: small Django-based box recommendation system, box internal dimensions, weight capacity, and cost minimization, AI_USAGE.md, test cases, and test run output."*

2. **Domain Modeling & Architectural Design**:
   > *"Design a clean 4-app Django architecture (`boxes`, `products`, `orders`, `recommendations`) with a dedicated `services` layer for the bin packing algorithm, keeping models focused on persistence and business logic separated."*

3. **Algorithmic Implementation**:
   > *"Implement a pure-Python 3D Bin Packing heuristic using the Extreme Points algorithm (EP-3D-BPP). Do not rely on external C-based or platform-dependent packages like py3dbp or cvxpy. Support 6-axis orthogonal rotations, strict 3D bounding box containment, and non-overlapping collision checks. Implement a box selector that minimizes box unit cost first, with volumetric fit as secondary criteria, and supports multi-box split partitioning as a fallback."*

4. **Testing & Edge Cases**:
   > *"Write a comprehensive Django test suite covering dimensional limits, weight capacity violations, 3D rotations, cost minimization, multi-box partitioning, model validations, and REST API endpoints. Verify that all 25 tests pass."*

---

## 3. What Output Was Accepted

- **App Structure & Django Configuration**:
  - The modular breakdown into `boxes`, `products`, `orders`, and `recommendations` was accepted as it provides clean separation of concerns.
  - Integration of `rest_framework` and `corsheaders` in `config/settings.py`.
- **Pure-Python Extreme Points 3D Bin Packing Engine**:
  - The `ItemToPack`, `PackedItem`, `PackingResult`, and `PackingEngine` dataclasses and placement logic.
  - The generation of extreme points $(x+dx, y, z), (x, y+dy, z), (x, y, z+dz)$ and sorting by lowest $Z$ coordinate first (bottom-to-top gravity packing).
  - The orthogonal rotation permutation algorithm generating up to 6 unique orientations per cuboid.
- **Data Seeding & Realistic Scenarios**:
  - The management command `python manage.py seed_data` generating 7 distinct box types (from extra-small mailers to heavy-duty crates) and 10 ecommerce items with varying aspect ratios and densities.
- **Interactive Web Interface & Three.js 3D Visualizer**:
  - The frontend templates (`base.html`, `dashboard.html`, `recommender.html`, `orders.html`, `boxes.html`) utilizing Tailwind CSS and Three.js with OrbitControls to render real-time 3D box packing layouts.

---

## 4. What Output Was Rejected or Modified

- **Rejection of External 3D Packing Libraries**:
  - Initial suggestions to install third-party libraries (such as `py3dbp` or other PyPI wheels) were rejected because third-party libraries often fail to build on Windows environments (lack of C++ build tools), have unfixed bugs with rotation handling, and hide the algorithmic logic.
  - **Modification**: A self-contained, pure-Python 3D Extreme Points heuristic was built directly in `recommendations/services/packing_engine.py`. This ensures zero native dependencies, 100% deterministic execution across any OS, and full transparency.
- **Modification of Multi-Box Partitioning**:
  - A naive fallback that simply reported an error when items didn't fit into a single box was rejected.
  - **Modification**: Built `_partition_multi_box()` using a greedy First-Fit Decreasing algorithm that groups items into minimal multiple boxes with an explicit `SPLIT_REQUIRED` status and cost aggregation.
- **Correction in Test Assumptions**:
  - In `tests/test_box_selector.py`, an initial test case assumed that 2 units of headphones ($18 \times 14 \times 8$ cm each) would fit into `TEST-S` ($20 \times 15 \times 10$ cm).
  - **AI Analysis & Fix**: The items' combined volume ($2 \times 2016 = 4,032\text{ cm}^3$) physically exceeds `TEST-S` volume ($3,000\text{ cm}^3$). The selector correctly rejected `TEST-S` and selected `TEST-M`. The test was modified to assert `TEST-M` for 2 units, and `TEST-S` for 1 unit, validating the physical precision of the engine.

---

## 5. Mistakes the AI Made & How They Were Resolved

1. **Static Files Directory Warning**:
   - During `python manage.py makemigrations`, Django emitted warning `(?: (staticfiles.W004) The directory ... in STATICFILES_DIRS does not exist)`.
   - **Resolution**: Created `static/` and `templates/` directories to resolve Django's check cleanly.
2. **Volumetric vs Dimensional Over-simplification**:
   - In early draft logic, simple volume checking ($\sum V_i \le V_{box}$) was proposed as the primary check.
   - **Resolution**: Intervened to ensure that 3D bounding box checks and coordinate placement are mandatory, because items of long aspect ratios (e.g. a 75cm poster tube) have low volume but cannot physically fit in square boxes.
3. **Pytest Settings Misconfiguration**:
   - Running `pytest` initially failed with `django.core.exceptions.ImproperlyConfigured: Requested setting REST_FRAMEWORK`.
   - **Resolution**: Standardized on Django's native test runner (`python manage.py test`), which properly boots settings, database fixtures, and migrations, and added a `pytest.ini` with `DJANGO_SETTINGS_MODULE = config.settings`.

---

## 6. How the Final Code Was Verified

1. **Automated Unit & Integration Test Suite**:
   - Ran `python manage.py test --verbosity=2`.
   - Verified that all **25 tests passed in 0.207s** without any errors or deprecation warnings.
2. **Database & Migrations Verification**:
   - Verified that all migrations apply cleanly on a fresh database: `python manage.py migrate`.
   - Verified schema consistency: `python manage.py makemigrations --check --dry-run`.
3. **Live End-to-End Simulation**:
   - Executed `python manage.py seed_data` to simulate real ecommerce orders.
   - Tested ad-hoc recommendation via `POST /api/recommend/` with curl/fetch payloads.
   - Verified warehouse audit trail explanations and Three.js 3D visualization rendering in the browser.
4. **CI/CD Pipeline Setup**:
   - Verified GitHub Actions workflow definition in `.github/workflows/django.yml` across Python 3.11 and 3.12.
