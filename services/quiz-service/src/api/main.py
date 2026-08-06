from fastapi import FastAPI

app = FastAPI(title="PANDORA quiz-service", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "quiz-service"}
