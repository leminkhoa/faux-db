import random

def add_vat(value, rate: float) -> str:
    return f"{value * (1 + rate):.2f}"
