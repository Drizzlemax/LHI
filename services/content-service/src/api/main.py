from fastapi import FastAPI

app = FastAPI(title="PANDORA content-service", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "content-service"}
