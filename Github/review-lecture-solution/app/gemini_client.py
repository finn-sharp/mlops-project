from google import genai

import os
from dotenv import load_dotenv
load_dotenv()

GEMINI_API = os.getenv("GEMINI_API")
client = genai.Client(api_key=GEMINI_API)
response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents="내용을 입력하시오"
)
print(response)