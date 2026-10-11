"""NTA 2025 tax calculations (Nigeria Tax Act 2025, effective Jan 1 2026)."""
from config import NTA_PIT_BANDS, CIT_RATE_SMALL, CIT_RATE_MEDIUM, CIT_RATE_LARGE, VAT_RATE, VAT_EXEMPTION_TURNOVER


def calculate_pit(taxable_income: float) -> float:
    """Personal Income Tax per NTA 2025 progressive bands."""
    tax = 0
    remaining = taxable_income
    for bracket_amount, rate in NTA_PIT_BANDS:
        if remaining <= 0:
            break
        taxable_at_rate = min(remaining, bracket_amount)
        tax += taxable_at_rate * rate
        remaining -= taxable_at_rate
    return round(tax, 2)


def calculate_cit(taxable_income: float, turnover: float) -> float:
    """Company Income Tax per NTA 2025: small 0%, medium 20%, large 30%."""
    if turnover < 25000000:
        return round(taxable_income * CIT_RATE_SMALL, 2)
    if turnover <= 100000000:
        return round(taxable_income * CIT_RATE_MEDIUM, 2)
    return round(taxable_income * CIT_RATE_LARGE, 2)


def is_vat_exempt(annual_turnover: float) -> bool:
    return annual_turnover < VAT_EXEMPTION_TURNOVER


def calculate_vat(sales: float, annual_turnover: float = None) -> float:
    if annual_turnover is not None and is_vat_exempt(annual_turnover):
        return 0.0
    return round(sales * VAT_RATE, 2)


calculate_pita = calculate_pit
calculate_cita = calculate_cit
