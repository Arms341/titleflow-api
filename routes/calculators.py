"""
routes/calculators.py  v2.0.0
Locked template — JARVIS title_company gig.
POST endpoints for all 11 calculator flavors. Service-layer does the math —
this file is pure HTTP plumbing.

v2.0.0: Added TruValue, BuyerCompensation, BuyNowVsLater, PriceVsRate,
  ExtraPayment, ScenarioCompare endpoints.
"""
import logging

from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from schemas.calculator import (
    BuydownInput, BuydownResult,
    BuyerCompensationInput, BuyerCompensationResult,
    BuyerEstimateInput, BuyerEstimateResult,
    BuyNowVsLaterInput, BuyNowVsLaterResult,
    ExtraPaymentInput, ExtraPaymentResult,
    HoldingCostInput, HoldingCostResult,
    PriceVsRateInput, PriceVsRateResult,
    ScenarioCompareInput, ScenarioCompareResult,
    SellerNetSheetInput, SellerNetSheetResult,
    SellVsRentInput, SellVsRentResult,
    TruValueInput, TruValueResult,
)
from services.title_calculator import CalculatorError, TitleCalculatorService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["calculators"])


def _get_calculator_service(db: Session = Depends(get_db)) -> TitleCalculatorService:
    inst = TitleCalculatorService()
    inst._db = db
    return inst


@router.post("/seller-net-sheet", response_model=SellerNetSheetResult, status_code=200)
def seller_net_sheet(data: SellerNetSheetInput, service: TitleCalculatorService = Depends(_get_calculator_service)):
    try:
        return service.seller_net_sheet(data)
    except CalculatorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("seller_net_sheet route error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/buyer-estimate", response_model=BuyerEstimateResult, status_code=200)
def buyer_estimate(data: BuyerEstimateInput, service: TitleCalculatorService = Depends(_get_calculator_service)):
    try:
        return service.buyer_estimate(data)
    except CalculatorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("buyer_estimate route error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sell-vs-rent", response_model=SellVsRentResult, status_code=200)
def sell_vs_rent(data: SellVsRentInput, service: TitleCalculatorService = Depends(_get_calculator_service)):
    try:
        return service.sell_vs_rent(data)
    except CalculatorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("sell_vs_rent route error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/holding-cost", response_model=HoldingCostResult, status_code=200)
def holding_cost(data: HoldingCostInput, service: TitleCalculatorService = Depends(_get_calculator_service)):
    try:
        return service.holding_cost(data)
    except CalculatorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("holding_cost route error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/buydown", response_model=BuydownResult, status_code=200)
def buydown(data: BuydownInput, service: TitleCalculatorService = Depends(_get_calculator_service)):
    try:
        return service.buydown(data)
    except CalculatorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("buydown route error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/truvalue", response_model=TruValueResult, status_code=200)
def truvalue(data: TruValueInput, service: TitleCalculatorService = Depends(_get_calculator_service)):
    try:
        return service.truvalue(data)
    except CalculatorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("truvalue route error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/buyer-compensation", response_model=BuyerCompensationResult, status_code=200)
def buyer_compensation(data: BuyerCompensationInput, service: TitleCalculatorService = Depends(_get_calculator_service)):
    try:
        return service.buyer_compensation(data)
    except CalculatorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("buyer_compensation route error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/buy-now-vs-later", response_model=BuyNowVsLaterResult, status_code=200)
def buy_now_vs_later(data: BuyNowVsLaterInput, service: TitleCalculatorService = Depends(_get_calculator_service)):
    try:
        return service.buy_now_vs_later(data)
    except CalculatorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("buy_now_vs_later route error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/price-vs-rate", response_model=PriceVsRateResult, status_code=200)
def price_vs_rate(data: PriceVsRateInput, service: TitleCalculatorService = Depends(_get_calculator_service)):
    try:
        return service.price_vs_rate(data)
    except CalculatorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("price_vs_rate route error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/extra-payment", response_model=ExtraPaymentResult, status_code=200)
def extra_payment(data: ExtraPaymentInput, service: TitleCalculatorService = Depends(_get_calculator_service)):
    try:
        return service.extra_payment(data)
    except CalculatorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("extra_payment route error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/scenario-compare", response_model=ScenarioCompareResult, status_code=200)
def scenario_compare(data: ScenarioCompareInput, service: TitleCalculatorService = Depends(_get_calculator_service)):
    try:
        return service.scenario_compare(data)
    except CalculatorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("scenario_compare route error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


calculators_router = router  # FIX-ROUTER-ALIAS
