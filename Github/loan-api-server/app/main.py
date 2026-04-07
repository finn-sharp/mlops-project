# Java로 치면, 컨트롤러의 역할이라고 함

from fastapi import FastAPI, HTTPException
import logging
from contextlib import asynccontextmanager
import os

from .model import LoanModel
from .schemas import LoanResponse, LoanRequest

# DEBUG
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models")
print(MODEL_DIR)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
        Description : 모델을 서버 실행 시 한번만 로드
    """
    logger.info('대출 심사 모델을 로드합니다')
    model = LoanModel()
    try : 
        model.load(model_dir=MODEL_DIR)
        logger.info('모델 로드 성공')
    except :
        logger.warning('모델 로드 실패')

        # DEBUG
        print(e)
        traceback.print_exc()

        logger.warning('/predict 엔드포인트는 모델 로드 후 사용가능')
    
    app.state.model = model

    yield 

    logger.info('대출 심사 API를 종료합니다')

app = FastAPI(
    title = '대출 심사 예측 API',
    description = 'ML 모델 기반 대출 승인 여부를 예측하는 API',
    version = '1.0.0',
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


# 머신러닝 예측하는 API 로직( 정의한 schema로 통신 )
@app.post("/predict", response_model= LoanResponse) # response_model을 다시 return해줘야 함
async def predict(request : LoanRequest):
    model = app.state.model

    try :    
        result = model.predict(request.model_dump()) # model_dump : key를 english로 변환
        return LoanResponse(**result) # dict, 가변인자처리법

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail="입력값 처리오류")
    except Exception as e:
        raise HTTPException(status_code=500)