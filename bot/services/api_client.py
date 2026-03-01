import logging
import os
from typing import Any

import httpx

BASE_URL = os.getenv("BACKEND_INTERNAL_URL", "http://backend:8000")
BOT_API_KEY = os.getenv("BOT_API_KEY", "")


class BackendClient:
    import logging
    log = logging.getLogger(__name__)
    async def bot_login(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{BASE_URL}/api/auth/bot-login",
                json=payload,
                headers={"X-BOT-API-KEY": BOT_API_KEY},
            )
            if r.status_code >= 400:
                log.error("bot-login failed: %s %s", r.status_code, r.text[:500])
            r.raise_for_status()
            return r.json()

    async def get_balance(self, token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{BASE_URL}/api/wallet/balance", headers={"Authorization": f"Bearer {token}"})
            r.raise_for_status()
            return r.json()

    async def rooms(self, token: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{BASE_URL}/api/bingo/rooms", headers={"Authorization": f"Bearer {token}"})
            r.raise_for_status()
            return r.json()

    async def join_room(self, token: str, room_id: int, cartela_id: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{BASE_URL}/api/bingo/join",
                json={"room_id": room_id, "cartela_id": cartela_id},
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()
            return r.json()

    async def cartelas(self, token: str, room_id: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{BASE_URL}/api/bingo/cartelas",
                params={"room_id": room_id},
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()
            return r.json()

    async def transactions(self, token: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{BASE_URL}/api/wallet/transactions", headers={"Authorization": f"Bearer {token}"})
            r.raise_for_status()
            return r.json()

    async def deposit_info(self, token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{BASE_URL}/api/wallet/deposit/info", headers={"Authorization": f"Bearer {token}"})
            r.raise_for_status()
            return r.json()

    async def submit_deposit(self, token: str, amount: str, telebirr_reference: str, sender_phone: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{BASE_URL}/api/wallet/deposit/submit",
                json={"amount": amount, "telebirr_reference": telebirr_reference, "sender_phone": sender_phone},
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()
            return r.json()

    async def deposit_status(self, token: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{BASE_URL}/api/wallet/deposit/status", headers={"Authorization": f"Bearer {token}"})
            r.raise_for_status()
            return r.json()

    async def submit_withdraw(self, token: str, amount: str, telebirr_phone: str, account_holder_name: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{BASE_URL}/api/wallet/withdraw/submit",
                json={"amount": amount, "telebirr_phone": telebirr_phone, "account_holder_name": account_holder_name},
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()
            return r.json()

    async def withdraw_status(self, token: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{BASE_URL}/api/wallet/withdraw/status", headers={"Authorization": f"Bearer {token}"})
            r.raise_for_status()
            return r.json()

    async def me(self, token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
            r.raise_for_status()
            return r.json()

    async def register_phone(self, token: str, phone_number: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{BASE_URL}/api/auth/register-phone",
                json={"phone_number": phone_number},
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()
            return r.json()
