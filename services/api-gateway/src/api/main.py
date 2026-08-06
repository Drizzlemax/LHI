from fastapi import FastAPI

app = FastAPI(title="PANDORA api-gateway", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "api-gateway"}
