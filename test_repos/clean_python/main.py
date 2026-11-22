from fastapi import FastAPI
import os

app = FastAPI(title="Clean Secure Python Microservice", version="1.0.0")

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "Clean Secure Service",
        "environment": os.getenv("ENV", "production")
    }

@app.get("/healthz")
def health_check():
    return {"status": "OK"}
