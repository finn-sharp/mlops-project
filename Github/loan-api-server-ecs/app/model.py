# Java, 서비스에 해당하는 파일이라고 함
import os
import logging
import joblib
import pandas as pd
from typing import Any

from pathlib import Path
from dotenv import load_dotenv
env_path = Path("__file__").resolve().parent / ".env"
load_dotenv(dotenv_path= env_path, override=False)

# 1. aws library
import boto3
import io

logger = logging.getLogger(__name__)


FIELD_TO_COLUMN = {
    "age": "나이",
    "gender": "성별",
    "annual_income": "연소득",
    "employment_years": "근속연수",
    "housing_type": "주거형태",
    "credit_score": "신용점수",
    "existing_loan_count": "기존대출건수",
    "annual_card_usage": "연간카드사용액",
    "debt_ratio": "부채비율",
    "loan_amount": "대출신청액",
    "loan_purpose": "대출목적",
    "repayment_method": "상환방식",
    "loan_period": "대출기간",
}


class LoanModel :
    def __init__(self):
        self.pipeline = None
        self.label_encoder: dict[str, Any] = {}
        self.feature_names: list[str] = []
        self.threshold: float = 0.5
        self.model_version: str = "1.1.1"

    # 2. 기존에 local에서 불러온 모델(loan_pipeline, label_encoders, feature_names)을 이제 AWS S3에서 불러오도록 수정 !!!!
    def load(self) -> None:
        bucket = os.environ.get("MODEL_BUCKET")
        prefix = os.environ.get("MODEL_PREFIX")        
        model = self._load_from_s3(bucket, prefix)
        return model
        
    def _load_from_s3(self, bucket: str, prefix: str) -> None:
        logger.info(f"S3에서 모델 로드: s3://{bucket}/{prefix}/")
        s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "ap-northeast-2"))

        self.pipeline = self._load_pkl_from_s3(s3, bucket, f"{prefix}/loan_pipeline.pkl")
        self.label_encoder = self._load_pkl_from_s3(s3, bucket, f"{prefix}/label_encoders.pkl")
        self.feature_names = self._load_pkl_from_s3(s3, bucket, f"{prefix}/feature_names.pkl")

        logger.info("S3 모델 로드 완료")

    @staticmethod
    def _load_pkl_from_s3(s3, bucket: str, key: str):
        response = s3.get_object(Bucket=bucket, Key=key)
        return joblib.load(io.BytesIO(response["Body"].read()))
    
    @staticmethod
    def _map_to_korean(data: dict[str, Any]) -> dict[str, Any]:
        return {FIELD_TO_COLUMN.get(k, k): v for k, v in data.items()}
    
    def predict(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.pipeline is None:
            raise RuntimeError("모델이 로드되지 않았습니다. load()함수를 먼저 호출하세요")
        
        mapped = self._map_to_korean(data)
        df = pd.DataFrame( [ mapped ] )[self.feature_names]

        # Encoding Module : Logic
        for col, encoder in self.label_encoder.items():
            df[col] = encoder.transform( df[col])
        
        # Result : Probability
        pos_p = round(float(self.pipeline.predict_proba(df)[0,1]),2)
        
        # T/F Cateria
        approved= pos_p >= self.threshold
        risk_grade = self._get_risk_grad(pos_p)

        return {
            "approved" : approved,
            "probability" : pos_p,
            "risk_grade" : risk_grade,
        }

        
    @staticmethod    
    def _get_risk_grad(pos_p:float) -> str :
        if pos_p >= 0.75:
            return "A"
        elif pos_p >= 0.5:
            return "B"
        elif pos_p >= 0.25:
            return "C"
        else :
            return "D"



