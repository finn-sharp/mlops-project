import os
import logging
from google import genai
import json
from typing import Any

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class ReviewAnalyzer :
    def __init__(self):
        self.client = genai.Client()
        gemini_api = os.environ.get('GEMINI_API')
        if not gemini_api:
            raise ValueError("Gemini API 키가 유효한지 확인하세요")
        genai.configure(api_key=gemini_api)
        self.model_version:str = '1.0.0'

    def analyst(self, data: dict[str, Any]) -> dict[str, Any]:
        prompt = f"""당신은 고객의 리뷰를 분석해야합니다. 
        결과값은 Json 형식으로만 응답하세요, 구체적인 답변은 아래 예시를 참고해주세요.

        [example]
        input : 배송이 너무 느려서 실망했어요. 상품 품질은 괜찮은데 포장이 엉망... 
        output : {{
                    "sentiment": "부정",
                    "category": "배송",
                    "summary": "배송 지연 및 포장 불량에 대한 불만",
                    "confidence": 0.85
        }}

        [criteria]
        답변 참고 시 참고할 기준 사항
        input에 대하여 아래 선지에 가장 적합한 것을 선택
        sentiment : [긍정 or 부정] 중 하나, 고객이 리뷰에 담은 분위기
        category : [배송, 상담, 주문] 중 하나, 고객이 이야기하는 서비스 항목
        summary : 전체 리뷰 내용에 대한 한줄 요약
        confidence : 0.0 ~ 1.0 사이값

        [실제 질문]
        input : {data}
        output :
        """ 

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        result = json.loads(response)

        return result