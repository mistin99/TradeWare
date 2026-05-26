# Project Setup

This guide will help you:
- Set up a virtual environment
- Install project dependencies
- Configure and use Alembic for database migrations

---

## 🔧 1. Set Up a Virtual Environment

### ✅ On Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

### ✅ On Windows

```bash
python -m venv venv
venv\Scripts\activate
```

---

## 📦 2. Install Dependencies

Make sure you have a `requirements.txt` file. Then run:

```bash
pip install -r requirements.txt
```

If you don’t have a `requirements.txt` yet, create one with:

```bash
pip freeze > requirements.txt
```

---


## 🔄 3. Alembic Setup

Alembic is used to manage schema migrations for SQLAlchemy-based applications.

### Step-by-Step

### ✅ Step 1: Install Alembic

```bash
pip install alembic
```

### ✅ Step 2: Initialize Alembic in your project

```bash
alembic init alembic
```

This creates an `alembic/` directory and an `alembic.ini` config file.

### ✅ Step 3: Configure Alembic

#### ✅ Update `alembic.ini`

Edit the `sqlalchemy.url` line to match your database connection string
Currently we override the ini setting for db url in alembic/env.py by using .env file variable

```ini
sqlalchemy.url = sqlite:///./test.db
# or for PostgreSQL:
# sqlalchemy.url = postgresql://user:password@localhost/dbname
```

#### ✅ Update `alembic/env.py`

Replace:

```python
target_metadata = None
```

With:

```python
from your_project.models import EntityBase  # Replace with your actual import
target_metadata = EntityBase.metadata
```

This allows Alembic to detect changes in your SQLAlchemy models.

### ✅ Step 4: Creating & Running Migrations

#### ✅ Create a Migration Script (Auto-Detect Changes)

```bash
alembic revision --autogenerate -m "Initial migration"
```

#### ✅ Apply the Migration to the Database

```bash
alembic upgrade head
```

#### ⬅️ Downgrade (Rollback) Last Migration

```bash
alembic downgrade -1
```

---
