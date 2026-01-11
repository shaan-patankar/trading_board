from __future__ import annotations


def format_product_label(name: str) -> str:
    return name.replace("_", " ").title()
