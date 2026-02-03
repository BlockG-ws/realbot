import logging
import traceback

from nio import MatrixRoom, AsyncClient, RoomMessageNotice
from config import config


async def copy_notice_as_text(client: AsyncClient, room: MatrixRoom, event: RoomMessageNotice):
    """
    If the incoming event is an m.notice, resend the same content as m.text
    preserving formatted body and the m.relates_to (reply) state.
    """
    enabled = config.is_feature_enabled('copy_notice_event', room_id=room.room_id)
    if not enabled:
        return
    src = getattr(event, "source", {}) or {}
    content = src.get("content", {})
    if content.get("msgtype") != "m.notice":
        return

    # Build new content preserving body, formatting and reply relations
    new_content = {"msgtype": "m.text"}

    original_sender = src.get("sender") or getattr(event, "sender", None)
    display_name = None
    if original_sender:
        # try to get display name from event unsigned or room member list
        unsigned = src.get("unsigned", {}) if isinstance(src, dict) else {}
        display_name = unsigned.get("display_name") or unsigned.get("prev_display_name")
        if not display_name and getattr(room, "members", None):
            member = getattr(room, "members", {}).get(original_sender)
            if member:
                display_name = getattr(member, "display_name", None) or getattr(member, "displayname", None)

    def _escape_html(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    original_sender_text = None
    if original_sender:
        original_sender_text = f"send by {original_sender}"
        if display_name:
            original_sender_text += f" ({display_name})"

    if "body" in content:
        body = content["body"]
        if original_sender_text:
            body = f"{body}\n\n{original_sender_text}"
        new_content["body"] = body
    elif original_sender_text:
        new_content["body"] = original_sender_text

    if "formatted_body" in content:
        if "format" in content:
            new_content["format"] = content["format"]
        formatted = content["formatted_body"]
        if original_sender_text:
            # append HTML-safe original sender information
            escaped = _escape_html(original_sender)
            formatted += f"<br><br><strong>Original sender:</strong> {escaped}"
            if display_name:
                formatted += f" ({_escape_html(display_name)})"
        new_content["formatted_body"] = formatted

    # Preserve reply state / relations (m.in_reply_to / other relations)
    if "m.relates_to" in content:
        new_content["m.relates_to"] = content["m.relates_to"]

    await client.room_send(
        room_id=room.room_id,
        message_type="m.room.message",
        content=new_content
    )
    # trying to delete message
    logging.debug("Copied notice event, trying to delete message")
    original_event_id = src.get("event_id") or getattr(event, "event_id", None)
    if original_event_id:
        try:
            redact_fn = getattr(client, "room_redact", None) or getattr(client, "redact", None)
            if redact_fn:
                await redact_fn(room.room_id, original_event_id)
        except Exception as e:
            logging.warning(f"Failed to redact event {original_event_id}\n{e}\n {traceback.format_exc()}")