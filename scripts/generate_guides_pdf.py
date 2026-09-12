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


def add_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(GREEN)
    canvas.rect(0, A4[1] - 8 * mm, A4[0], 8 * mm, fill=1, stroke=0)
    canvas.setFillColor(MUTED)
    canvas.setFont("KR", 8)
    canvas.drawString(18 * mm, 12 * mm, "오토블로그 AI")
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, f"{doc.page}")
    canvas.restoreState()


def build_admin(s, font):
    story = []
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("오토블로그 AI", s["sub"]))
    story.append(Paragraph("관리자 설정 · 운영 가이드", s["cover"]))
    story.append(
        Paragraph(
            "입금 확인 후 라이선스 키 발급 · 연장 · 고객 안내<br/>작성일: 2026-09-06",
            s["sub"],
        )
    )
    story.append(
        Paragraph(
            "관리자 웹페이지는 없습니다. 키는 Render 서버의 Admin API(터미널 curl)로만 발급합니다. "
            "노트북에서 manage.py만 실행하면 고객이 쓰는 서버에는 키가 생기지 않습니다.",
            s["warn"],
        )
    )

    story.append(Paragraph("1. 서비스 주소 (외울 것)", s["h1"]))
    story.append(
        table(
            ["구분", "URL"],
            [
                ["고객이 쓰는 화면 (핸드폰·PC 브라우저)", CUSTOMER_URL],
                ["서버 상태 확인", f"{ADMIN_BASE}/health"],
                ["키 발급 API (관리자 전용)", f"{ADMIN_BASE}/admin/licenses"],
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
                ["월간", "12,900원 / 30일"],
                ["연간", "129,000원 / 365일"],
                ["입금", "하나은행 365-910996-44807 (예금주: 신일)"],
                ["문의", "카톡/문자 010-7237-1258"],
                ["키 전달 목표", "입금 확인 후 약 10분 이내"],
            ],
            [40 * mm, 135 * mm],
            s,
        )
    )

    story.append(Paragraph("3. 한 번만 하는 준비", s["h1"]))
    story.append(bullets([
        "브라우저에서 dashboard.render.com 로그인 → 웹 서비스 blog-chrometool 열기",
        "Environment 메뉴에서 ADMIN_TOKEN 값을 복사한다. 이것이 관리자 비밀번호다.",
        "ADMIN_TOKEN이 비어 있으면 발급 API가 꺼져 있다. Render에 값을 넣고 재배포한다.",
        "토큰은 고객에게 절대 보내지 않는다.",
        "Mac에서 터미널 앱을 연다. 프로젝트 폴더로 이동할 필요는 없다.",
    ], font, s))

    story.append(Paragraph("4. 입금 후 키 발급 (매일 하는 일)", s["h1"]))
    story.append(Paragraph(
        "1) 통장 입금과 카톡/문자의 입금자명을 맞춘다.<br/>"
        "2) 아래 명령을 터미널에 붙여넣고, 여기토큰을 ADMIN_TOKEN으로, 홍길동을 실제 이름으로 바꾼다.<br/>"
        "3) 응답의 license_key를 카톡/문자로 보낸다.<br/>"
        "4) 고객에게 아래 URL에서 키를 넣고 [등록]하라고 안내한다.",
        s["body"],
    ))
    story.append(Paragraph("■ 월간 (30일)", s["h2"]))
    story.append(Paragraph(
        "curl -X POST https://blog-chrometool.onrender.com/admin/licenses<br/>"
        "  -H \"Content-Type: application/json\"<br/>"
        "  -H \"X-Admin-Token: 여기토큰\"<br/>"
        "  -d '{\"plan\": \"paid\", \"days\": 30, \"note\": \"홍길동 월결\"}'",
        s["code"],
    ))
    story.append(Paragraph("■ 연간 (365일)", s["h2"]))
    story.append(Paragraph(
        "curl -X POST https://blog-chrometool.onrender.com/admin/licenses<br/>"
        "  -H \"Content-Type: application/json\"<br/>"
        "  -H \"X-Admin-Token: 여기토큰\"<br/>"
        "  -d '{\"plan\": \"paid\", \"days\": 365, \"note\": \"홍길동 연결\"}'",
        s["code"],
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
        "구글/크롬 가입은 필요 없습니다.",
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
    story.append(Paragraph("부분 입금 시 연장 일수 = 입금액 ÷ 12,900 × 30 (소수점 버림). 예: 6,450원 → 15일.", s["body"]))
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
                ["체험", "trial", "1", "1", "1건 사용 즉시 종료"],
                ["지인", "family_free", "1", "30", "발급 후 약 1달"],
                ["유료", "paid", "3", "90", "월 12,900 / 연 129,000"],
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
        "사진 선택·자동 첨부는 아직 없다. 네이버 글쓰기에서 사진을 직접 첨부한다.",
        "폰에서는 글 생성 + 복사만 된다. 네이버 앱/모바일 글쓰기에 자동으로 넣지 못한다.",
        "Render 무료 플랜은 첫 접속이 30~60초 걸릴 수 있다.",
        "로컬 manage.py로 만든 키는 고객 화면에 등록되지 않는다. 반드시 위 curl(Render)로 발급한다.",
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
                ["한도 초과", "유료 일 3 / 월 90", "다음날 또는 한도 조정"],
            ],
            [40 * mm, 55 * mm, 80 * mm],
            s,
        )
    )
    return story


def build_customer(s, font):
    story = []
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("오토블로그 AI", s["sub"]))
    story.append(Paragraph("고객 사용 방법", s["cover"]))
    story.append(
        Paragraph(
            "핸드폰에서 3분 체크 → AI 초안 → 네이버 블로그에 붙여넣기<br/>작성일: 2026-09-06",
            s["sub"],
        )
    )

    story.append(Paragraph("1. 이용 주소 (이 주소만 저장하세요)", s["h1"]))
    story.append(Paragraph(f"<b>{CUSTOMER_URL}</b>", s["body"]))
    story.append(Paragraph(
        "핸드폰·태블릿·PC 브라우저에서 같습니다. 구글/크롬 회원가입은 필요 없습니다. "
        "관리자에게 받은 라이선스 키만 있으면 됩니다.",
        s["body"],
    ))

    story.append(Paragraph("2. 구독 · 입금", s["h1"]))
    story.append(
        table(
            ["항목", "내용"],
            [
                ["월간", "12,900원 (30일)"],
                ["연간", "129,000원 (365일)"],
                ["입금 계좌", "하나은행 365-910996-44807"],
                ["예금주", "신일"],
                ["입금 후 연락", "카톡/문자 010-7237-1258"],
                ["키 받는 시간", "확인 후 약 10분 이내"],
            ],
            [45 * mm, 130 * mm],
            s,
        )
    )
    story.append(Paragraph(
        "입금자명을 연락 주실 때 알려 주세요. 라이선스 키(예: ABCD-EFGH-IJKL)를 보내 드립니다. "
        "사이트에서 직접 결제하거나 키를 만드는 화면은 없습니다.",
        s["body"],
    ))

    story.append(Paragraph("3. 핸드폰에서 글 만들기 (기본)", s["h1"]))
    story.append(bullets([
        f"위 주소({CUSTOMER_URL})를 연다. 첫 화면은 30~60초 걸릴 수 있다.",
        "라이선스 키를 입력하고 [등록]을 누른다. 남은 기간·오늘 건수가 보이면 성공이다.",
        "업체 종류(설비 / 청소 / 직접입력)를 고른다.",
        "현장위치, 해결사항, 해결과정은 꼭 채운다. 나머지는 있으면 더 좋은 글이 나온다.",
        "[AI 블로그 글 생성하기]를 누른다.",
        "나온 글을 읽고 필요하면 고친 뒤 [전체 복사]를 누른다.",
        "네이버 블로그 글쓰기(앱 또는 PC)를 열고 붙여넣는다 (길게 누르기 → 붙여넣기, 또는 Ctrl+V / ⌘+V).",
        "사진은 네이버 글쓰기 화면에서 직접 첨부한다. 이 서비스에는 사진 자동 첨부가 없다.",
        "확인 후 네이버에서 [발행]한다.",
    ], font, s))

    story.append(Paragraph("4. PC 크롬 확장을 쓸 때", s["h1"]))
    story.append(bullets([
        "관리자에게 확장 설치 파일(zip)을 받거나, 안내받은 방법으로 Chrome에 설치한다.",
        "같은 라이선스 키를 확장 사이드패널에 넣고 [등록]한다.",
        "글을 생성한 뒤, 네이버 블로그 글쓰기 탭을 연 상태에서 [네이버 에디터로 보내기]를 누른다.",
        "제목·본문이 한 번에 안 들어가면: 본문 빈 칸을 한 번 클릭한 뒤 Ctrl+V / ⌘+V로 붙여넣는다. 확장이 본문을 클립보드에 넣어 둔다.",
        "사진은 네이버 에디터에서 첨부한다.",
    ], font, s))

    story.append(Paragraph("5. 알아 두실 점", s["h1"]))
    story.append(bullets([
        "유료 플랜은 하루 3건, 한 달 90건까지 생성할 수 있다.",
        "키는 핸드폰과 PC에서 같이 쓸 수 있다.",
        "크롬(구글) 아이디가 없어도 핸드폰 웹은 이용할 수 있다.",
        "네이버에 올리려면 네이버 로그인은 필요하다.",
        "키를 다른 사람에게 공유하지 마세요. 한도가 같이 깎입니다.",
        "문의: 카톡/문자 010-7237-1258",
    ], font, s))

    story.append(Paragraph("6. 안 될 때", s["h1"]))
    story.append(
        table(
            ["상황", "이렇게 해 보세요"],
            [
                ["등록이 안 됨", "키 철자(하이픈 포함)를 다시 확인. 입금 후 키를 받기 전이면 관리자에게 문의."],
                ["화면이 안 열리거나 매우 느림", "1분 기다렸다가 새로고침. 무료 서버가 잠에서 깨는 시간이다."],
                ["오늘 한도 초과", "다음날 다시 이용하거나 관리자에게 문의."],
                ["네이버에 글이 안 들어감", "복사 버튼 → 네이버 본문을 탭/클릭 → 붙여넣기."],
                ["사진", "네이버 글쓰기의 사진 첨부를 사용."],
            ],
            [50 * mm, 125 * mm],
            s,
        )
    )
    return story


def main():
    font = register_font()
    s = styles(font)
    DOCS.mkdir(exist_ok=True)

    admin_path = DOCS / "오토블로그_관리자_운영가이드.pdf"
    cust_path = DOCS / "오토블로그_고객_사용방법.pdf"

    for path, builder in ((admin_path, build_admin), (cust_path, build_customer)):
        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=18 * mm,
            title=path.stem,
            author="오토블로그 AI",
        )
        doc.build(builder(s, font), onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
