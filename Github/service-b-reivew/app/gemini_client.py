import os
import re
import logging
from google import genai
import json
from typing import Any

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class ReviewAnalyzer :
    def __init__(self):
        gemini_api = os.getenv('GEMINI_API')
        if not gemini_api:
            raise ValueError("Gemini API 키가 유효한지 확인하세요")
        
        self.client = genai.Client(api_key=gemini_api)
        self.model_version:str = '1.0.0'

    def test(self):
        test_prompt = "동작을 확인합니다, 대화 준비가 되었다면, 답변해주세요"
        response = self.client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=test_prompt
        )
        return response

    @staticmethod
    def parse_gemini_json(text: str) -> dict:
        """
        Gemini 모델이 반환한 Markdown 코드블록 JSON을 
        안전하게 파싱하여 dict로 반환
        """
        # ```json ... ``` 제거
        cleaned = re.sub(r"```json|```", "", text).strip()
    
        try:
            return json.loads(cleaned)
        
        except json.JSONDecodeError:
            logger.error(f"JSON 파싱 실패: {text}")
            return {"error": "JSON 파싱 실패", "raw": text}

    def analy(self, data: dict[str, Any]) -> dict[str, Any]:
        review_text = data.get("review_text","")
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
        sentiment : [긍정, 중립, 부정] 중 하나, 고객이 리뷰에 담은 분위기
        category : [배송, 품질, 가격, CS] 중 하나, 고객이 이야기하는 서비스 항목
        summary : 전체 리뷰 내용에 대한 한줄 요약
        confidence : 0.0 ~ 1.0 사이값

        [실제 질문]
        input : {review_text}
        output :
        """ 

        response = self.client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )

        # Gemini는 ```json (...) ``` 양식 처리가 있어 이걸 없애야함
        raw_text = getattr(response, "text", None) or getattr(response, "output_text", "")
        result = self.parse_gemini_json(raw_text)

        return result