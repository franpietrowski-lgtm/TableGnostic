"""Live session bus — chat broadcast + WebRTC mesh signalling relay.

The bus is engineered as a thin relay so the AV layer can be swapped to an
SFU (LiveKit / Daily / Agora) later without touching the session-state
routes that broadcast chat/dice/initiative events. Relay-only message
types pass through without inspection:

    presence:join / leave / room / av-state
    webrtc:offer  / answer / ice         (targeted, via `to: conn_id`)

REST endpoints push their own broadcasts through `broadcast(sid, payload)`.
"""
import json as _json
import secrets
from typing import Dict, List, Optional

from fastapi import WebSocket


class Peer:
    __slots__ = ("ws", "uid", "name", "conn_id")

    def __init__(self, ws, uid, name, conn_id):
        self.ws = ws
        self.uid = uid
        self.name = name
        self.conn_id = conn_id


class Bus:
    def __init__(self):
        self.rooms: Dict[str, List[Peer]] = {}

    async def join(self, sid: str, ws: WebSocket, uid: str, name: str) -> Peer:
        await ws.accept()
        peer = Peer(ws=ws, uid=uid, name=name, conn_id=secrets.token_urlsafe(8))
        self.rooms.setdefault(sid, []).append(peer)
        return peer

    def leave(self, sid: str, ws: WebSocket) -> Optional[Peer]:
        if sid not in self.rooms:
            return None
        gone = None
        kept = []
        for p in self.rooms[sid]:
            if p.ws is ws and gone is None:
                gone = p
            else:
                kept.append(p)
        self.rooms[sid] = kept
        return gone

    def peers(self, sid: str) -> List[Peer]:
        return list(self.rooms.get(sid, []))

    async def _safe_send(self, peer: Peer, payload: dict):
        try:
            await peer.ws.send_text(_json.dumps(payload, default=str))
            return True
        except Exception:
            return False

    async def send(self, sid: str, payload: dict, exclude_ws: Optional[WebSocket] = None):
        dead = []
        for p in list(self.rooms.get(sid, [])):
            if exclude_ws is not None and p.ws is exclude_ws:
                continue
            ok = await self._safe_send(p, payload)
            if not ok:
                dead.append(p)
        for p in dead:
            self.leave(sid, p.ws)

    async def send_to(self, sid: str, conn_id: str, payload: dict):
        for p in list(self.rooms.get(sid, [])):
            if p.conn_id == conn_id:
                ok = await self._safe_send(p, payload)
                if not ok:
                    self.leave(sid, p.ws)
                return


bus = Bus()


async def broadcast(sid: str, payload: dict):
    """Module-level convenience for routes that don't need direct bus access."""
    await bus.send(sid, payload)
