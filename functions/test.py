import random


def country_of_origin(full_name: bool = False) -> str:
    countries = [
        ("VNM", "Socialist Republic of Vietnam"),
        ("USA", "United States of America"),
        ("JPN", "Japan"),
        ("DEU", "Federal Republic of Germany"),
        ("GBR", "United Kingdom of Great Britain and Northern Ireland"),
        ("FRA", "French Republic"),
    ]
    code, long_name = random.choice(countries)
    return long_name if full_name else code
