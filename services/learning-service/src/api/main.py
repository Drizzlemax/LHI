from fastapi import FastAPI

app = FastAPI(title="PANDORA learning-service", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "learning-service"}
