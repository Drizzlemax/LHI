from fastapi import FastAPI

app = FastAPI(title="PANDORA crawler-service", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "crawler-service"}
