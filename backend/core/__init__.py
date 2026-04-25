"""Table-Gnostic core — shared infrastructure for the route modules.

The split mirrors the conceptual session-room layers the platform exposes
to every campaign:

    Voice/video       → core/bus.py + routes/sessions.py (WS layer)
    Table state       → routes/sessions.py (initiative, effects, scenes)
    Game actions      → routes/sessions.py (chat, dice, damage)
    Journal/log       → routes/characters.py (folio.journal endpoint)
    Presence          → core/bus.py (presence + WebRTC signalling relay)
    Roles             → core/security.py (player/gm/admin gating)

The current AV layer is mesh WebRTC; the bus is engineered so a future
LiveKit / Daily / Agora migration can swap the relay without touching
the session-state routes. See routes/sessions.py docstring for that plan.
"""
