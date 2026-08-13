# 러그 주문 문의 챗봇 (Claude + 네이버 톡톡)

## 구성 파일
- `size_matcher.py` : 사이즈-가격표 + "원하는 크기를 포함하는 가장 작은 규격 찾기" 계산 로직
- `main.py` : 네이버 톡톡 웹훅을 받아 Claude API로 답변을 만들고 다시 전송하는 서버
- `requirements.txt` : 필요한 패키지 목록

## 1. 매트샵 상품(2037769813) 기준으로 이미 채워둔 내용
- 사이즈: 100x150 / 140x200 / 170x230 / 200x290 (140x200 기준가 대비 차액 방식)
- 소재/세탁법/배송비/색상/주문제작(원형 가능) 안내 등 상세페이지 내용 반영 완료

### ⚠️ 딱 하나만 직접 채워주세요
`size_matcher.py` 맨 위 `BASE_PRICE_140x200 = 0` 부분에
**140x200 사이즈 실제 가격(원)** 을 넣어주세요.
(캡처에는 다른 사이즈와의 차액만 나와있어서 기준가 자체는 못 읽어왔어요.
 예: 140x200이 89,000원이면 `BASE_PRICE_140x200 = 89000`)

색상이 스크린샷에 보인 것보다 더 있다면 `AVAILABLE_COLORS` 목록에 추가해주세요.

## 2. 로컬 테스트
```bash
pip install -r requirements.txt

# 사이즈 계산 로직만 단독 테스트
python size_matcher.py

# 서버 실행 (환경변수 먼저 설정)
export ANTHROPIC_API_KEY=sk-ant-...
export TALKTALK_ACCESS_TOKEN=발급받은토큰
uvicorn main:app --reload
```

## 3. 배포
- 이 서버를 외부에서 접근 가능한 곳에 올려야 합니다 (예: Cafe24, AWS, Naver Cloud, Railway, Render 등)
- HTTPS 주소가 있어야 톡톡 웹훅 등록이 가능합니다

## 4. 네이버 톡톡 연결
1. [네이버 톡톡 파트너센터](https://partner.talk.naver.com) 가입 및 채널 개설
2. 개발자 도구 > 챗봇API 설정 메뉴에서 Access Token 발급
3. 발급받은 토큰을 서버 환경변수 `TALKTALK_ACCESS_TOKEN`에 등록
4. 배포한 서버의 `/webhook/talktalk` 주소를 톡톡 파트너센터의 Webhook URL로 등록

공식 참고 자료: https://github.com/navertalk/chatbot-api

## 5. 실제 톡톡 페이로드 형식 확인 필요
`main.py`의 `talktalk_webhook` 함수 안에서 요청 body를 파싱하는 부분
(`event`, `user`, `textContent.text` 필드명)은 위 공식 문서의
최신 스펙과 대조해서 필드명을 맞춰주세요. 톡톡 API 버전에 따라
필드 구조가 조금씩 다를 수 있습니다.

## 다음 단계로 추천하는 것
- 초기에는 견적 자동 응답 후 "최종 확인은 담당자가 도와드릴게요" 같은
  안전장치를 넣어 사람이 한 번 검수하는 흐름 추천
- 모양이 있는 주문(원형, 별모양 등)은 고객이 사진을 보내면
  Claude Vision으로 가로/세로 최대값(bounding box)만 추출해서
  동일한 사이즈 매칭 로직에 넣으면 됩니다
