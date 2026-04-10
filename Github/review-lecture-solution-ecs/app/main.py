from contextlib import asynccontextmanager
import datetime
from datetime import datetime
import json
import logging
import uuid
from xml.parsers.expat import model

from fastapi import FastAPI, HTTPException
from .gemini_client import ReviewAnalyzer
from .schemas import ReviewRequest, ReviewResponse

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):

    try : 
        app.state.analyzer = ReviewAnalyzer()
    except ValueError as e:
        logger.error("분석기 초기화 실패")
        raise 

    yield

    logger.info("서비스 종료 중...")

app = FastAPI(
    title = "고객 리뷰 분석 API",
    description = "Gemini LLM 기반 고객 리뷰 감성 분석 API",
    version = "1.0.0",
    lifespan = lifespan
)

@app.get("/health")
def health_check(self):
    return {"status" : "healthy"}

@app.post("/analyze", response_model=ReviewResponse)
def analyze_review(request : ReviewRequest):
    request_id = str(uuid.uuid4())
    start_time = datetime.now()

    try : 
    
        result = app.state.analyzer.analyze(request.review_text)
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000

        # CloudWatch에 남을 예측 로그**
        log_data = {
            "request_id": request_id,
            "timestamp": start_time.isoformat(),
            **request.model_dump(),
            "sentiment": result["approved"],
            "category": result["probability"],
            "summary": result["risk_grade"],
            "confidence": result["confidence"],
            "model_version": model.model_version,
            "latency_ms": round(latency_ms, 2)
        }
        logger.info(f"PREDICTION_LOG: {json.dumps(log_data, ensure_ascii=False)}")
        return ReviewResponse(**result)
    
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail="입력값 처리오류")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500)