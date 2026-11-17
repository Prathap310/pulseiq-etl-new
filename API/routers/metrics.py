from fastapi import APIRouter, HTTPException

from API.services.metrics_service import get_metric_data
from API.services.freshness_service import get_freshness
from API.services.lineage_service import get_metric_lineage

router = APIRouter(prefix="/api/v1", tags=["Metrics"])


@router.get("/metrics")
def list_metrics():
    return {
        "available_metrics": ["M01", "M07", "M13", "M22", "M27"],
        "count": 5,
    }


@router.get("/metrics/{metric_id}/lineage")
def metric_lineage(metric_id: str):
    try:
        return get_metric_lineage(metric_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/metrics/{metric_id}")
def metric_details(metric_id: str):
    try:
        return get_metric_data(metric_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve metric data.",
        )


@router.get("/freshness")
def data_freshness():
    return get_freshness()
