# Project Setup

This guide explains how to set up and run the project, including:
- Virtual environment setup
- Dependency installation (pyproject-based)
- Running the FastAPI application
- Database migrations with Alembic

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

This project uses pyproject.toml as the single source of truth for dependencies.

### ✅ Install project(recommended)
```bash
pip install -e .
```

### ✅ Install with development tools
```bash
pip install -e ".[dev]"
```

---


## 🔄 3. Running the application

### Step-by-Step

### ✅ Step 1: Start the FastAPI server

```bash
python -m uvicorn trade_ware.main:app --reload
```
