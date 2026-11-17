from fastapi import FastAPI

from API.routers.metrics import router as metrics_router

app = FastAPI(
    title="PulseIQ Metrics API",
    description=(
        "API for PulseIQ workforce, payroll, attendance, "
        "task completion, and attrition-risk metrics. "
        "Includes metric definitions, source information, "
        "data lineage, and freshness."
    ),
    version="1.0.0",
)

app.include_router(metrics_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "application": "PulseIQ Metrics API",
        "version": "1.0.0",
        "documentation": "/docs",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
