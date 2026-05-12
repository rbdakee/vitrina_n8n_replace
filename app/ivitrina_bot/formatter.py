from typing import Any


NO_RESULTS_TEXT = "Объектов не найдено\nПопробуйте сделать поиск по другим критериям"
SEPARATOR = "-" * 30


def _format_price(price: Any) -> str:
    if not price:
        return "Цена не указана"
    try:
        return f"{int(price):,} ₸".replace(",", " ")
    except (TypeError, ValueError):
        return f"{price} ₸"


def _build_link(item: dict[str, Any]) -> str | None:
    source = item.get("source")
    if source == "Витрина":
        return f"https://ivitrina.kz/real-property/{item.get('id')}"
    krisha_id = item.get("krisha_id")
    if krisha_id and krisha_id != "agent_taken":
        return f"https://krisha.kz/a/show/{krisha_id}"
    return None


def format_item(item: dict[str, Any]) -> str:
    source = item.get("source")
    link = _build_link(item)

    score = item.get("score")
    score_text = f"⭐️ {score}" if score is not None else ""

    price_text = _format_price(item.get("price"))
    area = item.get("area")
    area_text = f"{area} м²" if area else ""
    rooms = item.get("rooms_count")
    rooms_text = f"🛏 {rooms}" if rooms else ""

    contact_name = item.get("contact_name")
    contact_name_text = f"МОП: {contact_name}" if contact_name else ""

    contact_phone = item.get("contact_phone")
    if contact_phone:
        suffix = "" if source == "Крыша" else "ы"
        contact_phone_text = f"МОП контакт{suffix}: +7{contact_phone}"
        whatsapp_link = f'МОП: <a href="wa.me/7{contact_phone}">WhatsApp</a>'
    else:
        contact_phone_text = ""
        whatsapp_link = ""

    phones = item.get("phones")
    phones_text = ""
    if source == "Крыша" and item.get("krisha_id") != "agent_taken" and phones:
        phones_text = f"\n📱 Клиент: {phones}"

    complex_name = (item.get("complex") or "").strip() or "Не указано"
    lines: list[str] = [
        f"<b>ЖК: {complex_name}</b>",
        f"📍 {item.get('address') or 'Адрес не указан'}",
        f"💰 {price_text}",
    ]

    metrics = " | ".join(part for part in (area_text, rooms_text, score_text) if part)
    if metrics:
        lines.append(f"📏 {metrics}")

    if item.get("category"):
        lines.append(f"📋 Категория: {item['category']}")

    if contact_name_text:
        lines.append(contact_name_text)
    if contact_phone_text:
        lines.append(contact_phone_text)
    if whatsapp_link:
        lines.append(whatsapp_link)
    if phones_text:
        lines.append(phones_text.lstrip("\n"))

    lines.append("")
    lines.append(f"📌 Источник: {source}")
    if link:
        lines.append(f"🔗 Ссылка: {link}")
    lines.append(SEPARATOR)

    return "\n".join(lines) + "\n"


def format_results(items: list[dict[str, Any]]) -> str:
    if not items:
        return NO_RESULTS_TEXT
    return "".join(format_item(i) for i in items)
