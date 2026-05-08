"""Slack Bot Token 알림 유틸리티 (chat.postMessage)"""
import logging

import requests

logger = logging.getLogger(__name__)

_API_URL = "https://slack.com/api/chat.postMessage"


def send(token: str, channel: str, text: str) -> bool:
    """Slack Bot Token 으로 메시지 전송. 실패해도 예외를 던지지 않는다."""
    if not token or not channel:
        return False
    try:
        resp = requests.post(
            _API_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"channel": channel, "text": text},
            timeout=5,
        )
        data = resp.json()
        if not data.get("ok"):
            logger.warning(f"[Slack] 전송 실패: {data.get('error', 'unknown')}")
            return False
        return True
    except Exception as e:
        logger.warning(f"[Slack] 전송 오류: {e}")
        return False
