from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# -----------------------------------
# Logging Configuration
# -----------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# -----------------------------------
# FastAPI App Initialization
# -----------------------------------
app = FastAPI(
    title="AI Hallucination Detector",
    description="Backend API for detecting AI hallucinations and citation issues",
    version="1.0.0"
)

# -----------------------------------
# CORS Configuration
# -----------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------
# Health Check Endpoint
# -----------------------------------
@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)