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
