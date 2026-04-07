from fastapi import FastAPI, HTTPException
import logging
from contextlib import asynccontextmanager
import os

from .gemini_client import ReviewAnalyzer
from .schemas import AnalysisRequest, AnalysisResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """gemini client 동작 여부 확인"""

    logger.info('Gemini 분석 도구를 준비합니다')
    analyzer = ReviewAnalyzer()
    try : 
        analyzer.test()
        logger.info('Gemini 분석 도구가 준비되었습니다')
    except :
        logger.warning('Gemini 분석 도구 설정에 실패했습니다')
    app.state.analyzer = analyzer
    
    yield

    logger.info('고객 분석 API를 종료합니다')

app = FastAPI(
    title='고객 리뷰 분석 API',
    description='gemini api를 활용한 고객 리뷰 분석 결과 제공 API',
    version='1.0.0',
    lifespan = lifespan
)

@app.get('/')
async def root():
    return {'data':'서버동작'}

@app.get('/health')
async def health_check():
    analyzer = app.state.analyzer
    analyzer_loaded = analyzer is not None
    return {
        "status" : "healthy" if analyzer_loaded else "degraded",
        "analyzer_loaded" : analyzer_loaded
    }


@app.post('/analysis', response_model=AnalysisResponse)
async def analysis(request : AnalysisRequest):
    analyzer = app.state.analyzer

    try :
        result = analyzer.analy(request.model_dump())
        return AnalysisResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail="입력값 처리오류")
    except Exception as e:
        raise HTTPException(status_code=500)