import re
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Dict, Optional, Tuple


BASE12_DIGITS = "0123456789°¤"
_MARKED_VALUE_PATTERN = re.compile(r"%([^%\r\n]*)%")
_DECIMAL_PATTERN = re.compile(r"(?P<sign>[+-]?)(?P<whole>\d+)(?:[,.](?P<fraction>\d+))?")
_BASE12_PATTERN = re.compile(
    rf"(?P<sign>[+-]?)(?P<whole>[{re.escape(BASE12_DIGITS)}]+)"
    rf"(?:[,.](?P<fraction>[{re.escape(BASE12_DIGITS)}]+))?"
)

# Configure only verified equivalences:
# "SI abbreviation": {"aenor_unit": "Aënor unit", "si_per_aenor": "factor"}
# `si_per_aenor` means how many units of the SI abbreviation equal one Aënor unit.
# Example shape only: {"km": {"aenor_unit": "...", "si_per_aenor": "1"}}
UNIT_CONVERSIONS: Dict[str, Dict[str, str]] = {}


def _integer_to_base12(value: int) -> str:
    if value == 0:
        return "0"

    result = ""
    while value:
        result = BASE12_DIGITS[value % 12] + result
        value //= 12
    return result


def _integer_from_base12(value: str) -> int:
    result = 0
    for digit in value:
        result = result * 12 + BASE12_DIGITS.index(digit)
    return result


def _format_finite_fraction(value: Fraction, radix: int, digits: str) -> Optional[str]:
    sign = "-" if value < 0 else ""
    value = abs(value)
    integer, remainder = divmod(value.numerator, value.denominator)
    integer_text = _integer_to_base12(integer) if radix == 12 else str(integer)
    if remainder == 0:
        return sign + integer_text

    fractional_digits = []
    seen_remainders = set()
    while remainder:
        if remainder in seen_remainders:
            return None
        seen_remainders.add(remainder)
        remainder *= radix
        digit, remainder = divmod(remainder, value.denominator)
        fractional_digits.append(digits[digit])

    return sign + integer_text + "." + "".join(fractional_digits)


def _parse_decimal(value: str) -> Optional[Fraction]:
    if _DECIMAL_PATTERN.fullmatch(value) is None:
        return None
    try:
        return Fraction(Decimal(value.replace(",", ".")))
    except (InvalidOperation, ValueError, ZeroDivisionError):
        return None


def _parse_base12(value: str) -> Optional[Fraction]:
    match = _BASE12_PATTERN.fullmatch(value)
    if match is None:
        return None

    sign = -1 if match.group("sign") == "-" else 1
    whole = _integer_from_base12(match.group("whole"))
    fractional = match.group("fraction")
    if not fractional:
        return Fraction(sign * whole)

    denominator = 12 ** len(fractional)
    numerator = whole * denominator + _integer_from_base12(fractional)
    return Fraction(sign * numerator, denominator)


def decimal_to_base12(n):
    """Convertit un entier de base 10 en notation positionnelle base 12."""
    try:
        value = int(n)
    except (TypeError, ValueError):
        return str(n)
    sign = "-" if value < 0 else ""
    return sign + _integer_to_base12(abs(value))


def decimal_value_to_base12(value: str) -> Optional[str]:
    """Convertit une valeur décimale si son écriture en base 12 est finie."""
    parsed = _parse_decimal(value)
    if parsed is None:
        return None
    converted = _format_finite_fraction(parsed, 12, BASE12_DIGITS)
    if converted is None:
        return None
    separator = "," if "," in value else "."
    return converted.replace(".", separator)


def base12_to_decimal(value: str) -> Optional[str]:
    """Convertit une valeur en chiffres base 12 si son décimal est fini."""
    parsed = _parse_base12(value)
    if parsed is None:
        return None
    converted = _format_finite_fraction(parsed, 10, "0123456789")
    if converted is None:
        return None
    separator = "," if "," in value else "."
    return converted.replace(".", separator)


def _unit_factor(si_unit: str) -> Tuple[str, Fraction]:
    config = UNIT_CONVERSIONS[si_unit]
    aenor_unit = config.get("aenor_unit", "").strip()
    factor_text = config.get("si_per_aenor", "")
    factor = _parse_decimal(factor_text)
    if not aenor_unit or factor is None or factor <= 0:
        raise ValueError(f"Configuration d'unité invalide pour {si_unit!r}")
    return aenor_unit, factor


def _parse_marked_value(value: str) -> Optional[Tuple[str, str, str]]:
    match = re.fullmatch(
        r"(?P<leading>\s*)(?P<number>[+-]?\d+(?:[,.]\d+)?)"
        r"(?P<separator>\s*)(?P<unit>.*?)\s*",
        value,
    )
    if match is None:
        return None
    return match.group("leading"), match.group("number"), match.group("unit")


def process_aenor_numbers(text: str) -> str:
    """
    Convertit les valeurs base 10 balisées en base 12 et retire les balises.

    Une unité n'est convertie que si elle figure dans UNIT_CONVERSIONS. Une
    valeur dont la représentation base 12 serait périodique reste balisée.
    """
    def replace_match(match: re.Match) -> str:
        parsed = _parse_marked_value(match.group(1))
        if parsed is None:
            return match.group(0)

        leading, number, unit = parsed
        decimal_value = _parse_decimal(number)
        if decimal_value is None:
            return match.group(0)

        output_unit = unit
        if unit in UNIT_CONVERSIONS:
            output_unit, factor = _unit_factor(unit)
            decimal_value /= factor

        base12_value = _format_finite_fraction(decimal_value, 12, BASE12_DIGITS)
        if base12_value is None:
            return match.group(0)
        separator = "," if "," in number else "."
        base12_value = base12_value.replace(".", separator)
        suffix = f" {output_unit}" if output_unit else ""
        return f"{leading}{base12_value}{suffix}"

    return _MARKED_VALUE_PATTERN.sub(replace_match, text)


def prepare_aenor_numbers_for_translation(text: str) -> str:
    """
    Convertit les chiffres base 12 de la source en français décimal balisé.

    Les unités Aënor ne sont converties que lorsqu'une correspondance SI est
    explicitement configurée. Les valeurs non représentables en décimal fini
    restent balisées et inchangées.
    """
    reverse_units = {}
    for si_unit in UNIT_CONVERSIONS:
        aenor_unit, factor = _unit_factor(si_unit)
        if aenor_unit in reverse_units:
            raise ValueError(f"Unité Aënor ambiguë configurée : {aenor_unit!r}")
        reverse_units[aenor_unit] = (si_unit, factor)

    unit_pattern = "|".join(
        re.escape(unit) for unit in sorted(reverse_units, key=len, reverse=True)
    )
    unit_suffix_pattern = (
        rf"(?:(?P<space>\s+)(?P<unit>{unit_pattern}))?"
        if unit_pattern
        else ""
    )
    source_value_pattern = re.compile(
        rf"(?<![\w{re.escape(BASE12_DIGITS)}%])"
        rf"(?P<number>[+-]?[{re.escape(BASE12_DIGITS)}]+(?:[,.][{re.escape(BASE12_DIGITS)}]+)?)"
        + unit_suffix_pattern
        + rf"(?![\w{re.escape(BASE12_DIGITS)}%])"
    )

    def convert_value(match: re.Match, marked: bool) -> str:
        number = match.group("number")
        decimal_value = _parse_base12(number)
        if decimal_value is None:
            return match.group(0)

        unit = match.groupdict().get("unit")
        si_unit = None
        if unit:
            si_unit, factor = reverse_units[unit]
            decimal_value *= factor

        decimal_text = _format_finite_fraction(decimal_value, 10, "0123456789")
        if decimal_text is None:
            return match.group(0) if marked else f"%{match.group(0)}%"
        if "," in number:
            decimal_text = decimal_text.replace(".", ",")
        suffix = f" {si_unit}" if si_unit else ""
        return f"%{decimal_text}{suffix}%"

    def convert_marked(match: re.Match) -> str:
        inner = match.group(1)
        value_match = source_value_pattern.fullmatch(inner.strip())
        if value_match is None:
            return match.group(0)
        converted = convert_value(value_match, marked=True)
        return match.group(0) if converted == value_match.group(0) else converted

    def convert_unmarked(match: re.Match) -> str:
        return convert_value(match, marked=False)

    output = []
    last_end = 0
    for marked_match in _MARKED_VALUE_PATTERN.finditer(text):
        output.append(source_value_pattern.sub(convert_unmarked, text[last_end:marked_match.start()]))
        output.append(convert_marked(marked_match))
        last_end = marked_match.end()
    output.append(source_value_pattern.sub(convert_unmarked, text[last_end:]))
    return "".join(output)


def strip_number_markers(text: str) -> str:
    """Retire les balises numériques après que le LLM a traduit le texte."""
    return _MARKED_VALUE_PATTERN.sub(lambda match: match.group(1), text)


if __name__ == "__main__":
    print(process_aenor_numbers("Valeur : %30% ; fraction : %0,5%."))
