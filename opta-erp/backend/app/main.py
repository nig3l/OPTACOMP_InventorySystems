# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Import API routers
from .api import auth, inventory, sales

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Computer Hardware ERP API",
    description="API for managing computer hardware inventory and sales",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, will replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(sales.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Computer Hardware ERP API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)