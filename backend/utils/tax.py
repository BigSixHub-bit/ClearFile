from config import PITA_RATES, CITA_RATE_SMALL, CITA_RATE_LARGE, VAT_RATE


def calculate_pita(taxable_income: float) -> float:
    tax = 0
    remaining = taxable_income
    for bracket_amount, rate in PITA_RATES:
        if remaining <= 0:
            break
        taxable_at_rate = min(remaining, bracket_amount)
        tax += taxable_at_rate * rate
        remaining -= taxable_at_rate
    return round(tax, 2)


def calculate_cita(taxable_income: float, turnover: float) -> float:
    if turnover < 25000000:
        return round(taxable_income * CITA_RATE_SMALL, 2)
    return round(taxable_income * CITA_RATE_LARGE, 2)


def calculate_vat(sales: float) -> float:
    return round(sales * VAT_RATE, 2)
