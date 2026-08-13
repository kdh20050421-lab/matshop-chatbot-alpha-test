# main.py
# 네이버 톡톡 챗봇 API 웹훅을 받아서 Claude API로 답변을 만들고 다시 보내주는 서버.
#
# 실행 전 준비물:
#   1) pip install fastapi uvicorn httpx anthropic
#   2) 환경변수 설정
#        ANTHROPIC_API_KEY   - Anthropic 콘솔에서 발급
#        TALKTALK_ACCESS_TOKEN - 네이버 톡톡 파트너센터에서 발급 (챗봇API 설정 메뉴)
#   3) 서버를 배포한 뒤, 그 서버의 URL(예: https://yourdomain.com/webhook/talktalk)을
#      네이버 톡톡 파트너센터 > 챗봇API 설정 > Webhook URL에 등록
#
# 참고: 네이버 톡톡 챗봇 API 공식 문서/예제
#   https://github.com/navertalk/chatbot-api

import os
import re
import httpx
from fastapi import FastAPI, Request
from anthropic import Anthropic

from size_matcher import (
    find_best_option, format_answer, RUG_CATALOG,
    AVAILABLE_COLORS, CUSTOM_ORDER_INFO,
)

app = FastAPI()

anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

TALKTALK_ACCESS_TOKEN = os.environ.get("TALKTALK_ACCESS_TOKEN")
TALKTALK_SEND_URL = "https://gw.talk.naver.com/chatbot/v1/event"

# 매트샵(smartstore.naver.com/matshop) 상품번호 2037769813 상세페이지 기준
SYSTEM_PROMPT = f"""
당신은 "매트샵"의 러그 상품 고객 응대 챗봇입니다.
친절하고 간결하게 한국어로 답변하세요.

[상품 기본 정보]
- 상품명: 러그 거실 카페트 사이잘룩 먼지없는 단모 사계절 워셔블 (매트샵 자체제작 상품)
- 형태: 사각형 (주문제작 시 원형도 가능)
- 주요소재: 폴리에스테르 (사이잘룩, 단단하게 짜인 평직 카페트)
- 원산지: 국산(경기도), 국내생산 100%
- 뒷면: 미끄럼방지 도트처리

[판매 중인 규격/가격] (140x200 기준가 대비 차액)
{chr(10).join(f"- {o.name} : {o.price:,}원 (세탁기 용량 {o.washer_capacity} 필요)" for o in RUG_CATALOG)}

[색상 옵션 예시]
{', '.join(AVAILABLE_COLORS)} 등 (전체 옵션은 상품 페이지 참고 안내)

[제품 특징]
- 사계절 사용 가능, 뒤틀림 거의 없음, 고급스럽고 클래식한 느낌
- 먼지 날림이 적어 아이 있는 집에서도 사용 가능
- 반려동물 스크래치에 강함

[세탁 방법 안내]
- 물세탁 또는 세탁기 사용 가능 (울코스, 액체세제, 차가운 물)
- 탈수는 물기가 가실 정도로 3~5분만
- 섬유유연제, 표백제, 건조기 사용 금지 (변형/손상 위험)
- 세탁 시 이불세탁망 사용 권장

[배송 정보]
- 택배, 배송비 무료 / 제주 추가 3,000원, 그 외 도서지역 추가 4,000원

[주문제작 안내]
{CUSTOM_ORDER_INFO}
고객이 원하는 가로x세로 치수를 말하면, 그 치수를 포함할 수 있는
가장 작은 규격 원단을 재단해서 제작합니다.
사이즈가 애매하거나 원형 등 복잡한 모양이면 네이버 톡톡이나 전화상담(010-9101-8125)으로
연결해드리겠다고 안내하세요.
(치수를 아직 말하지 않았다면 가로/세로 치수를 먼저 물어보세요)
"""


def extract_size(text: str):
    """'130x150', '130X150', '130 x 150cm' 같은 패턴에서 가로/세로 숫자를 뽑아냄"""
    match = re.search(r"(\d{2,3})\s*[xX×]\s*(\d{2,3})", text)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None


def ask_claude(user_message: str, size_info: str = "") -> str:
    extra = f"\n\n[시스템이 미리 계산한 사이즈 매칭 결과]\n{size_info}" if size_info else ""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message + extra}],
    )
    return response.content[0].text


async def send_talktalk_message(user_id: str, text: str):
    """톡톡 사용자에게 텍스트 메시지 보내기"""
    payload = {
        "event": "send",
        "user": user_id,
        "textContent": {"text": text},
    }
    headers = {"Authorization": TALKTALK_ACCESS_TOKEN}

    async with httpx.AsyncClient() as client:
        await client.post(TALKTALK_SEND_URL, json=payload, headers=headers)


@app.post("/webhook/talktalk")
async def talktalk_webhook(request: Request):
    body = await request.json()

    # 톡톡에서 오는 이벤트 형식에 맞게 파싱 (실제 페이로드 구조는
    # 파트너센터 문서에서 최종 확인 후 필드명을 맞춰주세요)
    event = body.get("event")
    user_id = body.get("user")
    user_text = body.get("textContent", {}).get("text", "")

    if event != "send" or not user_text:
        return {"status": "ignored"}

    # 1) 치수가 포함된 메시지인지 먼저 규칙 기반으로 정확히 계산
    size = extract_size(user_text)
    size_info = ""
    if size:
        want_width, want_height = size
        size_info = format_answer(want_width, want_height)

    # 2) 계산 결과를 참고자료로 Claude에게 넘겨서 자연스러운 문장으로 답변 생성
    reply_text = ask_claude(user_text, size_info)

    # 3) 톡톡으로 답변 전송
    await send_talktalk_message(user_id, reply_text)

    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "alive"}
