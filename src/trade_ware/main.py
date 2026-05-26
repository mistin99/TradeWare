"""
Tests: 
Description: Main entry point of the application
"""

from fastapi import FastAPI

app  = FastAPI()

@app.get("/")
async def root():
    """Root endpoint of the app."""
    return {"message": "Hello, World!"}