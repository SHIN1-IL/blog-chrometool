#!/usr/bin/env python3
"""오토블로그 AI — 관리자 운영가이드 / 고객 사용방법 PDF 생성"""

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/Library/Fonts/AppleGothic.ttf",
    "/System/Library/Fonts/AppleGothic.ttf",
]

GREEN = HexColor("#03c75a")
DARK = HexColor("#0f172a")
MUTED = HexColor("#475569")
LINE = HexColor("#e2e8f0")
BG = HexColor("#f8fafc")
WARN = HexColor("#b45309")

CUSTOMER_URL = "https://blog-chrometool.onrender.com/app/"
ADMIN_BASE = "https://blog-chrometool.onrender.com"
WRITTEN = "2026-10-05"


def register_font() -> str:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont("KR", path))
            return "KR"
    raise FileNotFoundError("한글 폰트(AppleGothic)를 찾을 수 없습니다.")


def styles(font: str):
    base = getSampleStyleSheet()
    s = {
        "cover": ParagraphStyle(
            "cover",
            parent=base["Title"],
            fontName=font,
            fontSize=22,
            leading=30,
            textColor=DARK,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "sub": ParagraphStyle(
            "sub",
            parent=base["Normal"],
            fontName=font,
            fontSize=11,
            leading=16,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=16,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName=font,
            fontSize=14,
            leading=20,
            textColor=DARK,
            spaceBefore=14,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName=font,
            fontSize=12,
            leading=17,
            textColor=HexColor("#166534"),
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontName=font,
            fontSize=10,
            leading=15,
            textColor=DARK,
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "code": ParagraphStyle(
            "code",
            parent=base["Normal"],
            fontName=font,
            fontSize=8.5,
            leading=13,
            textColor=DARK,
            backColor=BG,
            leftIndent=4,
            rightIndent=4,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "warn": ParagraphStyle(
            "warn",
            parent=base["Normal"],
            fontName=font,
            fontSize=10,
            leading=15,
            textColor=WARN,
            spaceAfter=8,
        ),
        "cell": ParagraphStyle(
            "cell",
            parent=base["Normal"],
            fontName=font,
            fontSize=9,
            leading=13,
            textColor=DARK,
        ),
        "cellh": ParagraphStyle(
            "cellh",
            parent=base["Normal"],
            fontName=font,
            fontSize=9,
            leading=13,
            textColor=white,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontName=font,
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
    }
    return s


def bullets(items, font, s):
    lis = [
        ListItem(Paragraph(t, s["body"]), leftIndent=12, bulletColor=GREEN)
        for t in items
    ]
    return ListFlowable(
        lis,
        bulletType="bullet",
        start="•",
        leftIndent=18,
        bulletFontName=font,
        bulletFontSize=10,
    )


def table(headers, rows, col_widths, s):
    data = [[Paragraph(h, s["cellh"]) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), s["cell"]) for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GREEN),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("BACKGROUND", (0, 1), (-1, -1), white),
                ("FONTNAME", (0, 0), (-1, -1), s["body"].fontName),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return t


def page_chrome(brand):
    def add_header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(GREEN)
        canvas.rect(0, A4[1] - 8 * mm, A4[0], 8 * mm, fill=1, stroke=0)
        canvas.setFillColor(MUTED)
        canvas.setFont("KR", 8)
        canvas.drawString(18 * mm, 12 * mm, brand)
        canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, f"{doc.page}")
        canvas.restoreState()

    return add_header_footer


def build_admin(s, font):
    story = []
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("오토블로그 AI", s["sub"]))
    story.append(Paragraph("관리자 설정 · 운영 가이드", s["cover"]))
    story.append(
        Paragraph(
            f"입금 확인 후 라이선스 키 발급 · 연장 · 고객 안내<br/>작성일: {WRITTEN}",
            s["sub"],
        )
    )
    story.append(
        Paragraph(
            "키는 운영 콘솔(/ops/)에서 발급합니다. 노트북에서 manage.py만 실행하면 "
            "고객이 쓰는 서버에는 키가 생기지 않습니다.",
            s["warn"],
        )
    )

    story.append(Paragraph("1. 서비스 주소 (외울 것)", s["h1"]))
    story.append(
        table(
            ["구분", "URL"],
            [
                ["고객이 쓰는 화면 (핸드폰·PC 브라우저)", CUSTOMER_URL],
                ["운영 콘솔 (키 발급)", f"{ADMIN_BASE}/ops/"],
                ["서버 상태 확인", f"{ADMIN_BASE}/health"],
                ["Render 대시보드", "https://dashboard.render.com"],
            ],
            [70 * mm, 105 * mm],
            s,
        )
    )

    story.append(Paragraph("2. 요금 · 계좌 (고객 안내와 동일)", s["h1"]))
    story.append(
        table(
            ["항목", "내용"],
            [
                ["스탠다드", "월 12,900원 · 6개월 64,500원 · 연 129,000원"],
                ["스탠다드 내용", "네이버 블로그만 · 하루 1건 · 달 30건"],
                ["프리미엄", "월 24,900원 · 6개월 124,500원 · 연 249,000원"],
                ["프리미엄 내용", "블로그·당근·지도·카톡 · 하루 3건 · 달 90건"],
                ["입금", "하나은행 365-910996-44807 (예금주: 신일)"],
                ["입금 메모", "스탠다드 또는 프리미엄"],
                ["문의", "카톡/문자 070-8065-1258 · acrosstool@gmail.com"],
                ["키 전달 목표", "입금 확인 후 약 10분 이내"],
                ["같이 보낼 설명서", "스탠다드 PDF 또는 프리미엄 PDF 중 입금한 플랜"],
            ],
            [40 * mm, 135 * mm],
            s,
        )
    )

    story.append(Paragraph("3. 한 번만 하는 준비", s["h1"]))
    story.append(bullets([
        "브라우저에서 dashboard.render.com 로그인 → 웹 서비스 3minblog 열기",
        "Environment 메뉴에서 ADMIN_TOKEN 값을 복사한다. 이것이 관리자 비밀번호다.",
        "ADMIN_TOKEN이 비어 있으면 발급 API가 꺼져 있다. Render에 값을 넣고 재배포한다.",
        "토큰은 고객에게 절대 보내지 않는다.",
        "Mac에서 터미널 앱을 연다. 프로젝트 폴더로 이동할 필요는 없다.",
    ], font, s))

    story.append(Paragraph("4. 입금 후 키 발급 (매일 하는 일)", s["h1"]))
    story.append(Paragraph(
        f"1) 통장 입금과 카톡/문자의 입금자명·메모(스탠다드/프리미엄)를 맞춘다.<br/>"
        f"2) 운영 콘솔 {ADMIN_BASE}/ops/ 에 ADMIN_TOKEN으로 입장한 뒤, 해당 플랜 버튼을 누른다.<br/>"
        "3) 나온 키를 카톡/문자로 보내고, 그 플랜의 고객 설명서 PDF를 같이 보낸다.<br/>"
        "4) 고객에게 아래 URL에서 키를 넣고 [등록]하라고 안내한다.<br/>"
        "터미널로 발급할 때는 아래 curl을 쓴다. 여기토큰을 ADMIN_TOKEN으로, 홍길동을 실제 이름으로 바꾼다.",
        s["body"],
    ))
    story.append(Paragraph("■ 스탠다드 월간 (12,900원 · 30일)", s["h2"]))
    story.append(Paragraph(
        f"curl -X POST {ADMIN_BASE}/admin/licenses<br/>"
        "  -H \"Content-Type: application/json\"<br/>"
        "  -H \"X-Admin-Token: 여기토큰\"<br/>"
        "  -d '{\"plan\": \"paid_blog\", \"days\": 30, \"note\": \"홍길동 스탠다드\"}'",
        s["code"],
    ))
    story.append(Paragraph("■ 프리미엄 월간 (24,900원 · 30일)", s["h2"]))
    story.append(Paragraph(
        f"curl -X POST {ADMIN_BASE}/admin/licenses<br/>"
        "  -H \"Content-Type: application/json\"<br/>"
        "  -H \"X-Admin-Token: 여기토큰\"<br/>"
        "  -d '{\"plan\": \"paid_allin\", \"days\": 30, \"note\": \"홍길동 프리미엄\"}'",
        s["code"],
    ))
    story.append(Paragraph(
        "6개월은 days 180, 1년은 days 365. 스탠다드는 plan paid_blog, 프리미엄은 plan paid_allin.",
        s["body"],
    ))
    story.append(Paragraph(
        "성공 시 JSON에 license_key가 나온다. 예: K7P2-XXXX-XXXX 형태. 그 문자열만 고객에게 보낸다.",
        s["body"],
    ))

    story.append(Paragraph("■ 발급 목록 확인", s["h2"]))
    story.append(Paragraph(
        "curl https://blog-chrometool.onrender.com/admin/licenses<br/>"
        "  -H \"X-Admin-Token: 여기토큰\"",
        s["code"],
    ))

    story.append(Paragraph("■ 고객에게 보낼 문구 예시", s["h2"]))
    story.append(Paragraph(
        "입금 확인됐습니다.<br/>"
        "라이선스 키: (여기에 키)<br/>"
        "핸드폰에서 아래 주소를 열고 키를 넣은 뒤 [등록]을 눌러 주세요.<br/>"
        f"{CUSTOMER_URL}<br/>"
        "PC 크롬 확장을 쓰시면 같은 키를 확장에도 등록하면 됩니다.<br/>"
        "구글/크롬 가입은 필요 없습니다.<br/>"
        "스탠다드 고객에게는 스탠다드 설명서 PDF를, 프리미엄 고객에게는 프리미엄 설명서 PDF를 같이 보내세요.",
        s["code"],
    ))

    story.append(Paragraph("5. 체험 · 지인 · 연장 · 정지", s["h1"]))
    story.append(Paragraph("체험 (총 1건 후 종료)", s["h2"]))
    story.append(Paragraph(
        "-d '{\"plan\": \"trial\", \"days\": 30, \"note\": \"홍길동 체험\"}'",
        s["code"],
    ))
    story.append(Paragraph("지인 (일 1건 · 월 30건 · 1개월)", s["h2"]))
    story.append(Paragraph(
        "-d '{\"plan\": \"family_free\", \"months\": 1, \"note\": \"사촌\"}'",
        s["code"],
    ))
    story.append(Paragraph("연장 (같은 키, 고객 재입력 불필요)", s["h2"]))
    story.append(Paragraph(
        "curl -X POST https://blog-chrometool.onrender.com/admin/licenses/XXXX-XXXX-XXXX/extend<br/>"
        "  -H \"Content-Type: application/json\"<br/>"
        "  -H \"X-Admin-Token: 여기토큰\"<br/>"
        "  -d '{\"days\": 30}'",
        s["code"],
    ))
    story.append(Paragraph(
        "부분 입금 시 연장 일수(소수점 버림). "
        "스탠다드: 입금액 ÷ 12,900 × 30. 예: 6,450원 → 15일. "
        "프리미엄: 입금액 ÷ 24,900 × 30.",
        s["body"],
    ))
    story.append(Paragraph("정지 / 재활성화", s["h2"]))
    story.append(Paragraph(
        "정지: POST .../admin/licenses/키/suspend  (헤더에 X-Admin-Token만)<br/>"
        "재활성: POST .../admin/licenses/키/activate",
        s["code"],
    ))

    story.append(Paragraph("6. 플랜 한도", s["h1"]))
    story.append(
        table(
            ["플랜", "코드", "일일", "월간", "비고"],
            [
                ["스탠다드 체험", "trial_blog", "1", "1", "1건 사용 즉시 종료"],
                ["프리미엄 체험", "trial_allin", "1", "1", "1건 사용 즉시 종료"],
                ["스탠다드", "paid_blog", "1", "30", "월 12,900 / 6개월 64,500 / 연 129,000"],
                ["프리미엄", "paid_allin", "3", "90", "월 24,900 / 6개월 124,500 / 연 249,000"],
                ["관리자", "admin_test", "3", "무제한", "고정키 ADMIN-TEST (운영 서버에 두지 말 것)"],
            ],
            [28 * mm, 32 * mm, 22 * mm, 22 * mm, 71 * mm],
            s,
        )
    )

    story.append(Paragraph("7. 고객이 크롬에 가입해야 하나?", s["h1"]))
    story.append(bullets([
        "아니다. 라이선스는 구글 계정과 무관한 키 문자열이다.",
        "핸드폰만 쓰면 크롬 확장 없이 고객 URL만으로 글을 만들 수 있다.",
        "PC에서 네이버 에디터로 자동 넣기는 Chrome 브라우저 + 확장이 필요하다.",
        "Chrome 웹스토어에서 확장을 설치할 때만 구글 로그인이 필요할 수 있다. zip 직접 설치는 스토어 로그인 없이 가능하다.",
        "네이버 블로그 발행은 네이버 로그인이지 크롬 가입이 아니다.",
    ], font, s))

    story.append(Paragraph("8. 현재 제품 한계 (고객 문의 대비)", s["h1"]))
    story.append(bullets([
        "제목·본문 자동 주입: 확장의 [네이버 에디터로 보내기]가 시도한다. 스마트에디터가 바뀌면 실패할 수 있다. 실패 시 본문 칸 클릭 후 붙여넣기.",
        "사진 첨부하기는 초반현장, 중간과정1, 중간과정2, 중간과정3, 마무리현장의 5단계다. 단계마다 최대 10장, 합계 최대 50장이다.",
        "사진은 고객 기기에만 있다. AI로 전송하지 않으므로 사진 때문에 AI 비용이 늘지 않는다.",
        "복사와 네이버 에디터로 보내기는 글만 전달한다. 사진 파일은 들어가지 않는다. 고객은 본문의 【단계 이름】 아래에서 화면 사진을 1번부터 네이버에 첨부한다.",
        "폰에서는 글 생성 + 복사만 된다. 네이버 앱에 사진이 자동으로 꽂히지 않는다.",
        "Render 무료 플랜은 첫 접속이 30~60초 걸릴 수 있다.",
        "로컬 manage.py로 만든 키는 고객 화면에 등록되지 않는다. 운영 콘솔 또는 위 curl로 발급한다.",
    ], font, s))

    story.append(Paragraph("9. 자주 막는 오류", s["h1"]))
    story.append(
        table(
            ["증상", "원인", "조치"],
            [
                ["등록되지 않은 키", "로컬 DB에만 발급했거나 오타", "Render curl로 다시 발급, list로 확인"],
                ["401 / 인증 실패", "ADMIN_TOKEN 불일치", "Render Environment 값 재복사"],
                ["Admin API 비활성", "서버에 ADMIN_TOKEN 없음", "환경변수 추가 후 재배포"],
                ["첫 요청만 매우 느림", "Render 콜드스타트", "1분 대기 후 재시도"],
                ["한도 초과", "스탠다드 일 1·월 30 / 프리미엄 일 3·월 90", "다음날 또는 한도 조정"],
            ],
            [40 * mm, 55 * mm, 80 * mm],
            s,
        )
    )
    return story


def payment_rows(plan_rows):
    return plan_rows + [
        ["입금 계좌", "하나은행 365-910996-44807"],
        ["예금주", "신일"],
        ["입금 후 연락", "카톡/문자 070-8065-1258 · acrosstool@gmail.com"],
        ["키 받는 시간", "확인 후 약 10분 이내"],
    ]


def shared_start(story, s):
    story.append(Paragraph("1. 이용 주소 (이 주소만 저장하세요)", s["h1"]))
    story.append(Paragraph(f"<b>{CUSTOMER_URL}</b>", s["body"]))
    story.append(Paragraph(
        "핸드폰·태블릿·PC 브라우저에서 같습니다. 구글/크롬 회원가입은 필요 없습니다. "
        "관리자에게 받은 라이선스 키만 있으면 됩니다.",
        s["body"],
    ))


def shared_form_steps():
    return [
        f"위 주소({CUSTOMER_URL})를 연다. 첫 화면은 30~60초 걸릴 수 있다.",
        "라이선스 키를 입력하고 [등록]을 누른다. 플랜 이름과 남은 기간·오늘 건수가 보이면 성공이다.",
        "업체 종류(설비 / 청소 / 직접입력)를 고른다.",
        "현장위치, 해결사항, 해결과정, 글 스타일은 꼭 채운다. 나머지는 있으면 더 좋은 글이 나온다.",
    ]


def shared_notes(limit_line):
    return [
        limit_line,
        "키는 핸드폰과 PC에서 같이 쓸 수 있다.",
        "크롬(구글) 아이디가 없어도 핸드폰 웹은 이용할 수 있다.",
        "네이버에 올리려면 네이버 로그인은 필요하다.",
        "키를 다른 사람에게 공유하지 마세요. 한도가 같이 깎입니다.",
        "문의: 카톡/문자 070-8065-1258 · acrosstool@gmail.com",
    ]


def trouble_table(s, extra_rows):
    rows = [
        ["등록이 안 됨", "키 철자(하이픈 포함)를 다시 확인. 입금 후 키를 받기 전이면 관리자에게 문의."],
        ["화면이 안 열리거나 매우 느림", "1분 기다렸다가 새로고침. 서버가 잠에서 깨는 시간이다."],
        ["오늘 한도 초과", "다음날 다시 이용하거나 관리자에게 문의."],
        ["네이버에 글이 안 들어감", "복사 버튼 → 네이버 본문을 탭/클릭 → 붙여넣기."],
        ["사진이 붙여넣기에 없음", "복사는 글만 된다. 화면의 초반현장부터 1번 사진을 네이버 사진 첨부로 올린다."],
    ] + extra_rows
    return table(["상황", "이렇게 해 보세요"], rows, [50 * mm, 125 * mm], s)


def build_customer_standard(s, font):
    story = []
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("3분 블로그", s["sub"]))
    story.append(Paragraph("고객 사용 방법 · 스탠다드", s["cover"]))
    story.append(
        Paragraph(
            f"월 12,900원 · 네이버 블로그 초안<br/>작성일: {WRITTEN}",
            s["sub"],
        )
    )
    shared_start(story, s)

    story.append(Paragraph("2. 스탠다드 플랜", s["h1"]))
    story.append(
        table(
            ["항목", "내용"],
            payment_rows([
                ["플랜", "스탠다드"],
                ["월간", "12,900원 (30일)"],
                ["6개월", "64,500원 (180일, 1개월분 할인)"],
                ["연간", "129,000원 (365일, 2개월분 할인)"],
                ["나오는 글", "네이버 블로그 제목 · 본문 · 태그"],
                ["이용 한도", "하루 1건, 한 달 30건"],
            ]),
            [45 * mm, 130 * mm],
            s,
        )
    )
    story.append(Paragraph(
        "입금할 때 입금자명과 함께 메모에 「스탠다드」를 적어 주세요. "
        "라이선스 키(예: ABCD-EFGH-IJKL)를 보내 드립니다. "
        "사이트에서 직접 결제하거나 키를 만드는 화면은 없습니다. "
        "당근, 네이버 지도, 카톡 문구는 프리미엄 플랜에서 나옵니다. 스탠다드 화면에는 블로그 결과만 보입니다.",
        s["body"],
    ))

    story.append(Paragraph("3. 핸드폰에서 블로그 글 만들기", s["h1"]))
    story.append(bullets(shared_form_steps() + [
        "13. 사진 첨부하기에서 초반현장, 중간과정1, 중간과정2, 중간과정3, 마무리현장에 사진을 넣는다. 단계마다 10장, 합계 50장까지. 사진은 기기에만 남고 AI로 보내지 않는다.",
        "[오늘 현장 일기 만들기]를 누른다. 이 한 번이 하루 1건으로 잡힌다.",
        "블로그 본문은 【초반현장】부터 【마무리현장】 순서로 나뉜다. 각 단계 아래에 그 사진이 1번부터 보인다.",
        "[블로그 전체 복사] 후 네이버 글쓰기에 붙여넣는다. 복사되는 것은 글이다.",
        "붙여넣은 뒤 【초반현장】 문단 다음에 화면의 초반현장 1번 사진부터 첨부하고, 같은 방식으로 다음 단계도 넣는다.",
        "확인 후 네이버에서 [발행]한다.",
    ], font, s))

    story.append(Paragraph("4. PC 크롬 확장을 쓸 때", s["h1"]))
    story.append(bullets([
        "관리자에게 확장 설치 파일(zip)을 받거나, 안내받은 방법으로 Chrome에 설치한다.",
        "같은 라이선스 키를 확장 사이드패널에 넣고 [등록]한다. 플랜이 스탠다드로 보여야 한다.",
        "글을 생성한 뒤, 네이버 블로그 글쓰기 탭을 연 상태에서 [네이버 에디터로 보내기]를 누른다. 들어가는 것은 글이다.",
        "제목·본문이 한 번에 안 들어가면: 본문 빈 칸을 한 번 클릭한 뒤 Ctrl+V / ⌘+V로 붙여넣는다.",
        "사진은 화면의 초반현장부터 1번 순서대로 네이버 에디터에서 첨부한다.",
    ], font, s))

    story.append(Paragraph("5. 알아 두실 점", s["h1"]))
    story.append(bullets(shared_notes(
        "스탠다드는 하루 1건, 한 달 30건까지 만들 수 있다. 한 건을 만들면 블로그 초안 1개가 나온다."
    ), font, s))

    story.append(Paragraph("6. 안 될 때", s["h1"]))
    story.append(trouble_table(s, [
        ["당근·지도·카톡이 안 보임", "스탠다드에는 없는 화면이다. 필요하면 프리미엄(월 24,900원)으로 문의."],
    ]))
    return story


def build_customer_premium(s, font):
    story = []
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("3분 블로그", s["sub"]))
    story.append(Paragraph("고객 사용 방법 · 프리미엄", s["cover"]))
    story.append(
        Paragraph(
            f"월 24,900원 · 블로그 · 당근 · 네이버 지도 · 카톡<br/>작성일: {WRITTEN}",
            s["sub"],
        )
    )
    shared_start(story, s)

    story.append(Paragraph("2. 프리미엄 플랜", s["h1"]))
    story.append(
        table(
            ["항목", "내용"],
            payment_rows([
                ["플랜", "프리미엄"],
                ["월간", "24,900원 (30일)"],
                ["6개월", "124,500원 (180일, 1개월분 할인)"],
                ["연간", "249,000원 (365일, 2개월분 할인)"],
                ["나오는 글", "블로그, 당근, 네이버 지도, 카톡"],
                ["이용 한도", "하루 3건, 한 달 90건"],
            ]),
            [45 * mm, 130 * mm],
            s,
        )
    )
    story.append(Paragraph(
        "입금할 때 입금자명과 함께 메모에 「프리미엄」을 적어 주세요. "
        "라이선스 키(예: ABCD-EFGH-IJKL)를 보내 드립니다. "
        "사이트에서 직접 결제하거나 키를 만드는 화면은 없습니다. "
        "한 번 만들면 네 채널 초안이 같이 나오고, 그 한 번이 이용 1건입니다.",
        s["body"],
    ))

    story.append(Paragraph("3. 핸드폰에서 글 만들기", s["h1"]))
    story.append(bullets(shared_form_steps() + [
        "13. 사진 첨부하기에서 초반현장, 중간과정1, 중간과정2, 중간과정3, 마무리현장에 사진을 넣는다. 단계마다 10장, 합계 50장까지. 사진은 AI로 보내지 않는다.",
        "[오늘 현장 광고 만들기]를 누른다. 이 한 번이 하루 1건으로 잡힌다. 하루 최대 3번이다.",
        "결과 칸에 블로그, 당근, 지도, 카톡 탭이 나온다. 블로그 본문은 다섯 단계로 나뉘고, 각 단계 사진이 1번부터 보인다.",
    ], font, s))

    story.append(Paragraph("4. 네 가지 결과를 올리는 방법", s["h1"]))
    story.append(Paragraph("블로그", s["h2"]))
    story.append(bullets([
        "[블로그 전체 복사]를 누른 뒤 네이버 블로그 글쓰기에 붙여넣는다. 글만 복사된다.",
        "【초반현장】부터 【마무리현장】 순서로, 화면의 해당 단계 사진을 1번부터 네이버에 첨부한다.",
        "짧은 영상은 본문에 표시된 자리에 네이버에서 직접 넣는다.",
        "확인 후 네이버에서 [발행]한다.",
    ], font, s))
    story.append(Paragraph("당근", s["h2"]))
    story.append(bullets([
        "[당근 문구 복사]를 누른다.",
        "당근 앱에서 동네 글쓰기를 열고 붙여넣은 뒤 사진을 첨부하고 올린다.",
    ], font, s))
    story.append(Paragraph("네이버 지도", s["h2"]))
    story.append(bullets([
        "리뷰 요청 문자는 [문자 복사] 후 고객에게 문자로 보낸다.",
        "플레이스 소식은 [소식 복사] 후 네이버 플레이스 소식에 붙여넣는다.",
        "키워드는 [키워드 복사] 후 플레이스 소개나 소식에 활용한다.",
    ], font, s))
    story.append(Paragraph("카톡", s["h2"]))
    story.append(bullets([
        "고객 카톡은 [고객 카톡 복사] 후 작업한 고객 대화에 붙여넣는다.",
        "채널/단골 소식은 [채널 소식 복사] 후 카카오 채널 소식에 붙여넣는다.",
    ], font, s))

    story.append(Paragraph("5. PC 크롬 확장을 쓸 때", s["h1"]))
    story.append(bullets([
        "관리자에게 확장 설치 파일(zip)을 받거나, 안내받은 방법으로 Chrome에 설치한다.",
        "같은 라이선스 키를 확장 사이드패널에 넣고 [등록]한다. 플랜이 프리미엄으로 보여야 한다.",
        "블로그는 네이버 글쓰기 탭을 연 상태에서 [네이버 에디터로 보내기]를 누른다. 안 들어가면 본문 칸을 클릭한 뒤 Ctrl+V / ⌘+V. 들어가는 것은 글이다.",
        "블로그 사진은 화면의 초반현장부터 1번 순서대로 네이버에 첨부한다.",
        "당근, 지도, 카톡은 각 탭의 복사 버튼으로 복사해 해당 앱에 붙여넣는다. 그 채널 사진은 각 앱에서 따로 고른다.",
    ], font, s))

    story.append(Paragraph("6. 알아 두실 점", s["h1"]))
    story.append(bullets(shared_notes(
        "프리미엄은 하루 3건, 한 달 90건까지 만들 수 있다. 한 건마다 블로그·당근·지도·카톡이 함께 나온다."
    ), font, s))

    story.append(Paragraph("7. 안 될 때", s["h1"]))
    story.append(trouble_table(s, [
        ["탭이 블로그만 보임", "등록된 키가 스탠다드일 수 있다. 키와 플랜 이름을 관리자에게 확인."],
        ["당근·지도·카톡에 안 올라감", "각 탭에서 복사한 뒤, 그 앱의 글쓰기 칸을 눌러 붙여넣기."],
    ]))
    return story


def write_pdf(path, story, brand="오토블로그 AI", doc_title=None):
    chrome = page_chrome(brand)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title=doc_title or path.stem,
        author=brand,
    )
    doc.build(story, onFirstPage=chrome, onLaterPages=chrome)
    print(f"wrote {path}")


def main():
    font = register_font()
    s = styles(font)
    DOCS.mkdir(exist_ok=True)

    write_pdf(DOCS / "오토블로그_관리자_운영가이드.pdf", build_admin(s, font))
    write_pdf(
        DOCS / "3분블로그_고객_사용방법_스탠다드.pdf",
        build_customer_standard(s, font),
        brand="3분 블로그",
        doc_title="3분 블로그 고객 사용 방법 · 스탠다드",
    )
    write_pdf(
        DOCS / "3분블로그_고객_사용방법_프리미엄.pdf",
        build_customer_premium(s, font),
        brand="3분 블로그",
        doc_title="3분 블로그 고객 사용 방법 · 프리미엄",
    )
    for stale in (
        "오토블로그_고객_사용방법_스탠다드.pdf",
        "오토블로그_고객_사용방법_프리미엄.pdf",
    ):
        old_named = DOCS / stale
        if old_named.exists():
            old_named.unlink()
            print(f"removed {old_named}")

    old = DOCS / "오토블로그_고객_사용방법.pdf"
    if old.exists():
        old.unlink()
        print(f"removed {old}")


if __name__ == "__main__":
    main()
