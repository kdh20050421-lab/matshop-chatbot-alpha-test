# size_matcher.py
# 매트샵(smartstore.naver.com/matshop) 실제 상품 옵션 기준
# 상품명: 러그 거실 카페트 사이잘룩 먼지없는 단모 사계절 워셔블 140x200
# 상품번호: 2037769813

from dataclasses import dataclass

# ⚠️ 140x200 기준가만 실제 숫자로 바꿔주세요. (스크린샷엔 차액만 나와있어서 기준가를 못 읽었어요)
BASE_PRICE_140x200 = 98000  # 100x150(62,500원) + 차액 35,500원 역산

@dataclass
class RugOption:
    name: str
    width: int   # cm
    height: int  # cm
    price: int   # 원
    washer_capacity: str  # 세탁 시 필요한 세탁기 용량


# 실제 판매 옵션 (사이즈 4종, 기준가 대비 차액 반영)
RUG_CATALOG = [
    RugOption("100x150", 100, 150, BASE_PRICE_140x200 - 35500, "13kg"),
    RugOption("140x200", 140, 200, BASE_PRICE_140x200, "13kg"),
    RugOption("170x230", 170, 230, BASE_PRICE_140x200 + 20000, "16kg 이상"),
    RugOption("200x290", 200, 290, BASE_PRICE_140x200 + 59500, "25kg 이상"),
]

# 색상 옵션 (일부 예시 - 실제로는 더 많음: 그레이, 브라운, 베이지, 딥그레이, 다크그레이, 골드베이지, 에메랄드그레이 등)
AVAILABLE_COLORS = ["그레이", "브라운", "베이지", "딥그레이", "다크그레이", "골드베이지", "에메랄드그레이"]

# 주문제작 관련 (상세페이지 안내 내용)
CUSTOM_ORDER_INFO = (
    "주문 제작이 가능한 제품입니다. 원형(circle)도 제작 가능하며, "
    "정확한 상담은 네이버 톡톡이나 고객센터(010-9101-8125)로 문의 부탁드립니다."
)


def find_best_option(want_width: float, want_height: float):
    candidates = []
    for opt in RUG_CATALOG:
        fits_normal = (opt.width >= want_width) and (opt.height >= want_height)
        fits_rotated = (opt.width >= want_height) and (opt.height >= want_width)
        if fits_normal or fits_rotated:
            candidates.append(opt)

    if not candidates:
        return None
    return min(candidates, key=lambda o: o.width * o.height)


def format_answer(want_width: float, want_height: float) -> str:
    best = find_best_option(want_width, want_height)

    if best is None:
        max_opt = max(RUG_CATALOG, key=lambda o: o.width * o.height)
        return (
            f"요청하신 {want_width}x{want_height}cm 사이즈는 "
            f"현재 판매 중인 최대 규격({max_opt.name})보다 커서 "
            f"별도 상담이 필요합니다. {CUSTOM_ORDER_INFO}"
        )

    waste_note = ""
    if best.width != want_width or best.height != want_height:
        waste_note = f" ({best.name} 원단에서 {want_width}x{want_height}cm 크기로 재단해드립니다)"

    return (
        f"{want_width}x{want_height}cm 사이즈는 "
        f"{best.name} 규격(가격 {best.price:,}원)으로 제작 가능합니다.{waste_note} "
        f"(세탁 시 세탁기 용량 {best.washer_capacity} 필요)"
    )


if __name__ == "__main__":
    tests = [(130, 150), (90, 140), (250, 300), (150, 130)]
    for w, h in tests:
        print(f"{w}x{h} ->", format_answer(w, h))
