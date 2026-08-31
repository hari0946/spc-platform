"""POST /analysis/historical, GET /analysis, GET /analysis/{analysis_id}"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_historical_analysis_service
from app.schemas.analysis import AnalysisSummaryResponse, HistoricalAnalysisRequest, SPCAnalysisResultResponse
from app.services.historical_analysis_service import HistoricalAnalysisService

router = APIRouter(tags=["historical-analysis"])


@router.post("/analysis/historical", response_model=SPCAnalysisResultResponse)
async def run_historical_analysis(
    request: HistoricalAnalysisRequest,
    service: HistoricalAnalysisService = Depends(get_historical_analysis_service),
) -> SPCAnalysisResultResponse:
    result = await service.run_historical_analysis(
        upload_id=request.upload_id,
        parameter_id=request.parameter_id,
        machine_id=request.machine_id,
        product_id=request.product_id,
        operation_id=request.operation_id,
        spc_configuration_id=request.spc_configuration_id,
    )
    return SPCAnalysisResultResponse.model_validate(result)


@router.get("/analysis", response_model=list[AnalysisSummaryResponse])
async def list_analyses(
    analysis_type: Optional[str] = Query(None, description="HISTORICAL or MANUAL_CHECK_CURRENT"),
    machine_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    parameter_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    service: HistoricalAnalysisService = Depends(get_historical_analysis_service),
) -> list[AnalysisSummaryResponse]:
    results = await service.list_recent(
        analysis_type=analysis_type, machine_id=machine_id, product_id=product_id,
        parameter_id=parameter_id, limit=limit,
    )
    return [AnalysisSummaryResponse.model_validate(r) for r in results]


@router.get("/analysis/{analysis_id}", response_model=SPCAnalysisResultResponse)
async def get_analysis(
    analysis_id: str, service: HistoricalAnalysisService = Depends(get_historical_analysis_service)
) -> SPCAnalysisResultResponse:
    result = await service.get_analysis(analysis_id)
    return SPCAnalysisResultResponse.model_validate(result)
