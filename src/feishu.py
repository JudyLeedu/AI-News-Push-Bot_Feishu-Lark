"""飞书开放平台 API 客户端"""
import time
import httpx
from src.config import get_config


class FeishuClient:
    """飞书 API 客户端，管理 token 和消息发送"""

    def __init__(self):
        cfg = get_config()["feishu"]
        self.app_id = cfg["app_id"]
        self.app_secret = cfg["app_secret"]
        self._tenant_token: str | None = None
        self._token_expire: float = 0

    # ---------- 鉴权 ----------
    async def _get_tenant_token(self) -> str:
        """获取 tenant_access_token，自动缓存与刷新"""
        if self._tenant_token and time.time() < self._token_expire - 60:
            return self._tenant_token

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                json={"app_id": self.app_id, "app_secret": self.app_secret},
            )
            data = resp.json()
            if data.get("code") != 0:
                raise RuntimeError(f"获取 tenant token 失败: {data}")

            self._tenant_token = data["tenant_access_token"]
            self._token_expire = time.time() + data.get("expire", 7200)
            return self._tenant_token

    async def _headers(self) -> dict:
        token = await self._get_tenant_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    # ---------- 用户 ----------
    async def get_user_by_email(self, email: str) -> str | None:
        """通过邮箱查询用户 open_id"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://open.feishu.cn/open-apis/contact/v3/users/batch_get_id",
                headers=await self._headers(),
                json={"emails": [email]},
            )
            data = resp.json()
            if data.get("code") != 0:
                print(f"[Feishu] 查询用户失败: {data}")
                return None
            users = data.get("data", {}).get("user_list", [])
            if users:
                return users[0].get("user_id")
            return None

    # ---------- 发送卡片消息 ----------
    async def send_card(self, open_id: str, card: str) -> bool:
        """发送飞书卡片消息到指定用户单聊"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://open.feishu.cn/open-apis/im/v1/messages",
                headers=await self._headers(),
                params={"receive_id_type": "open_id"},
                json={
                    "receive_id": open_id,
                    "msg_type": "interactive",
                    "content": card,  # card 已经是 JSON 字符串
                },
            )
            data = resp.json()
            if data.get("code") != 0:
                print(f"[Feishu] 发送消息失败: {data}")
                return False
            print(f"[Feishu] 消息发送成功, message_id={data.get('data', {}).get('message_id')}")
            return True
