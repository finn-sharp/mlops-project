from pydantic import BaseModel, Field

class AnalysisRequest(BaseModel):
    """Review 데이터 입력 스키마"""
    review_text:str = Field(
        ...,
        description="리뷰 원문",
        examples=["배송이 너무 느려서 실망했어요. 상품 품질은 괜찮은데 포장이 엉망..."]
    )
    
    model_config = {
        "json_schema_extra" : {
            "examples" : [
                {
                    "review_text": "배송이 너무 느려서 실망했어요. 상품 품질은 괜찮은데 포장이 엉망..."
                }
            ]
        }
    }

class AnalysisResponse(BaseModel):
    sentiment : str = Field(
        ...,
        description="감정분석 ('긍정', '중립', '부정')",
    )
    category : str = Field(
        ...,
        description="서비스유형 [배송, 품질, 가격, CS]",
    )
    summary : str = Field(
        ...,
        description="불만 사항에 대한 요약",
    )
    confidence : float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="?? 확률 (0.0 ~ 1.0)",
    )