"""
NYSE 장 시간 유틸리티
- pytz 로 섬머타임(EDT/EST) 자동 처리  → UTC-4(여름) / UTC-5(겨울)
- pandas_market_calendars 로 공휴일 · 단축거래일 감지
  (미설치 시 주말만 제외하고 동작)
"""
from datetime import datetime, time as dtime
from typing import Literal, Optional, Tuple

import pytz

# ── 타임존 ────────────────────────────────────────────────────────
ET = pytz.timezone("America/New_York")   # DST 자동 처리: EDT(UTC-4) / EST(UTC-5)

MarketSession = Literal["pre_market", "market", "after_hours", "closed", "holiday"]

# NYSE 기본 거래 시간 (ET) — 단축거래일은 캘린더로 덮어씀
_PRE_OPEN       = dtime(4,  0)
_REGULAR_OPEN   = dtime(9, 30)
_REGULAR_CLOSE  = dtime(16,  0)
_AFTER_CLOSE    = dtime(20,  0)

# ── NYSE 캘린더 (선택적) ──────────────────────────────────────────
try:
    import pandas_market_calendars as mcal
    _nyse    = mcal.get_calendar("NYSE")
    _USE_CAL = True
except ImportError:
    _USE_CAL = False

# ── 내부 헬퍼 ─────────────────────────────────────────────────────

def now_et() -> datetime:
    """현재 미국 동부 시각 (섬머타임 자동 반영)"""
    return datetime.now(ET)


def _today_schedule() -> Optional[Tuple[dtime, dtime]]:
    """
    오늘 NYSE 정규장 open / close 시각 (ET time 객체) 반환.
    휴장일(공휴일 포함)이면 None 반환.
    단축거래일(예: 추수감사절 다음날, 크리스마스 전날)도 정확히 처리.
    """
    et_now = now_et()
    if et_now.weekday() >= 5:          # 주말
        return None

    if not _USE_CAL:                    # 캘린더 미설치 — 공휴일 무시
        return _REGULAR_OPEN, _REGULAR_CLOSE

    date_str = et_now.strftime("%Y-%m-%d")
    try:
        sched = _nyse.schedule(start_date=date_str, end_date=date_str)
        if sched.empty:
            return None                 # 공휴일
        row = sched.iloc[0]
        mkt_open  = row["market_open" ].to_pydatetime().astimezone(ET).time()
        mkt_close = row["market_close"].to_pydatetime().astimezone(ET).time()
        return mkt_open, mkt_close
    except Exception:
        return _REGULAR_OPEN, _REGULAR_CLOSE  # 오류 시 기본값


# ── 공개 API ──────────────────────────────────────────────────────

def get_session(dt: Optional[datetime] = None) -> MarketSession:
    """현재(또는 지정) 시각의 NYSE 세션 반환."""
    dt = dt or now_et()

    schedule = _today_schedule()
    if schedule is None:
        return "holiday"

    mkt_open, mkt_close = schedule
    t = dt.time()

    if mkt_open <= t < mkt_close:
        return "market"
    if _PRE_OPEN <= t < mkt_open:
        return "pre_market"
    if mkt_close <= t < _AFTER_CLOSE:
        return "after_hours"
    return "closed"


def is_market_open(dt: Optional[datetime] = None) -> bool:
    return get_session(dt) == "market"


SESSION_LABEL = {
    "market":      "정규장  (09:30–16:00 ET)",
    "pre_market":  "프리장  (04:00–09:30 ET)",
    "after_hours": "애프터장 (16:00–20:00 ET)",
    "closed":      "장 마감",
    "holiday":     "휴장일 (공휴일/주말)",
}

SESSION_COLOR = {
    "market":      "#00C853",
    "pre_market":  "#FFA000",
    "after_hours": "#FFA000",
    "closed":      "#8b949e",
    "holiday":     "#8b949e",
}


def session_label(session: MarketSession) -> str:
    return SESSION_LABEL.get(session, session)


def session_color(session: MarketSession) -> str:
    return SESSION_COLOR.get(session, "#c9d1d9")


def et_clock_str() -> str:
    """로그·UI용: 현재 ET 시각 문자열 (EDT/EST 표시)"""
    et_now = now_et()
    return et_now.strftime("%H:%M:%S %Z")   # 예: "09:35:42 EDT"
