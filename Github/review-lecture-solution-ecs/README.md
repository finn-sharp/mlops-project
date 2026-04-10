# review-lecture-solution

`review-lecture-solution` 폴더는 리뷰 강의 예제와 실습을 위한 프로젝트입니다.

## 구성

- `README.md` : 프로젝트 개요와 사용 방법
- `.gitignore` : Git에서 제외할 파일 목록
- `requirements.txt` : Python 패키지 의존성 목록

## 설치

```bash
cd Github/review-lecture-solution
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## 실행

필요한 스크립트나 노트북이 있다면 다음과 같이 실행합니다.

```bash
python main.py
```

또는 Jupyter 노트북 사용 시:

```bash
jupyter notebook
```

## 추가 안내

- `.venv`, `env` 등 가상환경 폴더는 `.gitignore`에 포함되어 추적되지 않습니다.
- 실제 코드가 추가되면 README 내용을 프로젝트에 맞게 수정하세요.