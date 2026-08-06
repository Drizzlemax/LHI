from fastapi import FastAPI

app = FastAPI(title="PANDORA recommendation-service", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "recommendation-service"}
