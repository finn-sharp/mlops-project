# Java로 치면, 컨트롤러의 역할이라고 함

from datetime import datetime
import json
import uuid

from fastapi import FastAPI, HTTPException
import logging
from contextlib import asynccontextmanager
import os

from .model import LoanModel
from .schemas import LoanResponse, LoanRequest

from pathlib import Path
from dotenv import load_dotenv
env_path = Path("__file__").resolve().parent / ".env"
load_dotenv(dotenv_path= env_path, override=False)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
        Description : 모델을 서버 실행 시 한번만 로드
    """
    logger.info('대출 심사 모델을 로드합니다')
    model = LoanModel()
    try : 
        model.load()
        logger.info('모델 로드 성공')
    except :
        logger.warning('모델 로드 실패')
        logger.warning('/predict 엔드포인트는 모델 로드 후 사용가능')
    
    app.state.model = model

    yield 

    logger.info('대출 심사 API를 종료합니다')

app = FastAPI(
    title = '대출 심사 예측 API',
    description = 'ML 모델 기반 대출 승인 여부를 예측하는 API',
    version = '1.1.1',
    # 이렇게 인자로 넣어주면, app실행 시 lifespan 함수를 실행시켜 줌
    lifespan = lifespan
)

@app.get('/')
async def root():
    return {"data" : "서버동작"}

# 서버가 살아있는지 체크하는 것 : 로드밸런서가 서버 생존 여부를 체크함***
# 새로운 컴퓨터를 띄우는 역할 : ECS in AWS***
@app.get('/health')
async def health_check():
    model = app.state.model
    model_loaded = model.pipeline is not None
    return {
        "status" : "healthy" if model_loaded else "degraded",
        "model_loaded" : model_loaded
    }


# 기존 예측에 추가적으로 log를 남기는 코드를 추가함
@app.post("/predict", response_model=LoanResponse)
async def predict(request: LoanRequest):
    model = app.state.model
    request_id = str(uuid.uuid4())
    start_time = datetime.now()

    try:
        result = model.predict(request.model_dump())
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000

        # CloudWatch에 남을 예측 로그**
        log_data = {
            "request_id": request_id,
            "timestamp": start_time.isoformat(),
            **request.model_dump(),
            "approved": result["approved"],
            "probability": result["probability"],
            "risk_grade": result["risk_grade"],
            "model_version": model.model_version,
            "latency_ms": round(latency_ms, 2)
        }
        # ecs에서 설정만 해주면, logger를 cloudwatch로 보내는 작업해줄 수 있음** 
        # 그래서 코드 레벨 에서는 logger로 정의하고 나면 신경 안써도 됨**
        logger.info(f"PREDICTION_LOG: {json.dumps(log_data, ensure_ascii=False)}")

        return LoanResponse(**result)

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail="입력값처리오류")
    except Exception as e:
        raise HTTPException(status_code=500)