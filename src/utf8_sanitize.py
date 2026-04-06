def sanitize_utf8(text: str) -> str:
    """Remove/replace caracteres que não podem ser codificados em UTF-8 (ex.: surrogates órfãos)."""
    if not text:
        return text
    return text.encode("utf-8", errors="replace").decode("utf-8")
