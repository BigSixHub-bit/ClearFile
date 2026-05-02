import io
import csv
import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from database import db
from utils.auth import get_current_user
from utils.tax import calculate_pita, calculate_cita, calculate_vat

router = APIRouter()


@router.get("/export/transactions")
async def export_transactions(
    format: str = Query("csv", enum=["csv", "json"]),
    period: str = Query("all", enum=["month", "year", "all"]),
    user: dict = Depends(get_current_user)
):
    if user.get("subscription_plan") == "starter":
        raise HTTPException(status_code=403, detail="Export requires Growth or Business plan")

    now = datetime.now(timezone.utc)
    query = {"user_id": user["id"]}

    if period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query["created_at"] = {"$gte": start_date.isoformat()}
    elif period == "year":
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        query["created_at"] = {"$gte": start_date.isoformat()}

    transactions = await db.transactions.find(query, {"_id": 0}).sort("date", -1).to_list(10000)

    if format == "json":
        return StreamingResponse(
            io.BytesIO(json.dumps(transactions, indent=2).encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=clearfileng_transactions_{period}.json"}
        )

    output = io.StringIO()
    if transactions:
        fieldnames = ["date", "type", "category", "description", "amount"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for tx in transactions:
            writer.writerow({
                "date": tx.get("date", ""),
                "type": tx.get("type", ""),
                "category": tx.get("category", ""),
                "description": tx.get("description", ""),
                "amount": tx.get("amount", 0)
            })

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=clearfileng_transactions_{period}.csv"}
    )


@router.get("/export/tax-report")
async def export_tax_report(
    format: str = Query("json", enum=["json", "csv", "pdf"]),
    user: dict = Depends(get_current_user)
):
    if user.get("subscription_plan") == "starter":
        raise HTTPException(status_code=403, detail="Export requires Growth or Business plan")

    user_id = user["id"]
    business_type = user.get("business_type", "freelancer")
    user_name = user.get("name", "User")

    transactions = await db.transactions.find({"user_id": user_id}, {"_id": 0}).to_list(10000)

    gross_income = sum(tx["amount"] for tx in transactions if tx["type"] == "income")
    total_expenses = sum(tx["amount"] for tx in transactions if tx["type"] == "expense")

    expense_by_category = {}
    income_by_category = {}
    for tx in transactions:
        cat = tx.get("category", "Miscellaneous")
        if tx["type"] == "expense":
            expense_by_category[cat] = expense_by_category.get(cat, 0) + tx["amount"]
        else:
            income_by_category[cat] = income_by_category.get(cat, 0) + tx["amount"]

    deductible_categories = ["Rent", "Utilities", "Professional Fees", "Marketing", "Equipment", "Subscriptions"]
    deductible_expenses = sum(expense_by_category.get(cat, 0) for cat in deductible_categories)
    taxable_income = max(0, gross_income - deductible_expenses)

    if business_type == "company":
        income_tax = calculate_cita(taxable_income, gross_income)
        tax_type = "Company Income Tax (CITA)"
    else:
        income_tax = calculate_pita(taxable_income)
        tax_type = "Personal Income Tax (PITA)"

    vat = calculate_vat(gross_income) if business_type in ["sme", "company"] else 0

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tax_year": datetime.now().year,
        "business_type": business_type,
        "tax_type": tax_type,
        "summary": {
            "gross_income": gross_income,
            "total_expenses": total_expenses,
            "deductible_expenses": deductible_expenses,
            "taxable_income": taxable_income,
            "income_tax": income_tax,
            "vat": vat,
            "total_tax_owed": income_tax + vat
        },
        "income_breakdown": income_by_category,
        "expense_breakdown": expense_by_category,
        "deductible_categories": {cat: expense_by_category.get(cat, 0) for cat in deductible_categories},
        "transaction_count": len(transactions),
        "disclaimer": "This report is for guidance only. Consult a certified tax professional for official filing."
    }

    if format == "json":
        return StreamingResponse(
            io.BytesIO(json.dumps(report, indent=2).encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=clearfileng_tax_report_{datetime.now().year}.json"}
        )

    if format == "pdf":
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='CustomTitle', fontSize=24, alignment=TA_CENTER, textColor=colors.HexColor('#006400'), spaceAfter=20))
        styles.add(ParagraphStyle(name='SectionHeader', fontSize=14, textColor=colors.HexColor('#006400'), spaceBefore=15, spaceAfter=10, fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='Normal_Right', fontSize=10, alignment=TA_RIGHT))

        elements = []
        elements.append(Paragraph("ClearFile NG", styles['CustomTitle']))
        elements.append(Paragraph("Tax Report", styles['Heading2']))
        elements.append(Spacer(1, 20))

        info_data = [
            ["Prepared For:", user_name],
            ["Tax Year:", str(datetime.now().year)],
            ["Business Type:", business_type.title()],
            ["Tax Type:", tax_type],
            ["Generated:", datetime.now().strftime("%B %d, %Y")]
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 30))

        elements.append(Paragraph("Tax Summary", styles['SectionHeader']))

        summary_data = [
            ["Description", "Amount (N)"],
            ["Gross Income", f"{gross_income:,.2f}"],
            ["Total Expenses", f"({total_expenses:,.2f})"],
            ["Deductible Expenses", f"({deductible_expenses:,.2f})"],
            ["Taxable Income", f"{taxable_income:,.2f}"],
            ["", ""],
            ["Income Tax", f"{income_tax:,.2f}"],
            ["VAT (7.5%)", f"{vat:,.2f}"],
            ["TOTAL TAX OWED", f"{income_tax + vat:,.2f}"]
        ]

        summary_table = Table(summary_data, colWidths=[4*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006400')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F5E9')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 30))

        if income_by_category:
            elements.append(Paragraph("Income Breakdown", styles['SectionHeader']))
            income_data = [["Category", "Amount (N)"]]
            for cat, amount in income_by_category.items():
                income_data.append([cat, f"{amount:,.2f}"])
            income_table = Table(income_data, colWidths=[4*inch, 2*inch])
            income_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006400')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(income_table)
            elements.append(Spacer(1, 20))

        if expense_by_category:
            elements.append(Paragraph("Expense Breakdown", styles['SectionHeader']))
            expense_data = [["Category", "Amount (N)", "Deductible"]]
            for cat, amount in expense_by_category.items():
                deductible = "Yes" if cat in deductible_categories else "No"
                expense_data.append([cat, f"{amount:,.2f}", deductible])
            expense_table = Table(expense_data, colWidths=[3*inch, 2*inch, 1*inch])
            expense_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006400')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(expense_table)
            elements.append(Spacer(1, 30))

        elements.append(Paragraph("Disclaimer", styles['SectionHeader']))
        elements.append(Paragraph(
            "This report is generated by ClearFile NG for informational purposes only. "
            "It does not constitute professional tax advice. Please consult a certified "
            "tax professional or the Federal Inland Revenue Service (FIRS) for official tax filing.",
            styles['Normal']
        ))
        elements.append(Spacer(1, 40))
        elements.append(Paragraph("Generated by ClearFile NG - Nigerian Tax & Expense Management",
                                  ParagraphStyle(name='Footer', fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))

        doc.build(elements)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=clearfileng_tax_report_{datetime.now().year}.pdf"}
        )

    # CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ClearFile NG Tax Report"])
    writer.writerow(["Generated", report["generated_at"]])
    writer.writerow(["Tax Year", report["tax_year"]])
    writer.writerow(["Business Type", business_type])
    writer.writerow(["Tax Type", tax_type])
    writer.writerow([])
    writer.writerow(["SUMMARY"])
    writer.writerow(["Gross Income", f"N{gross_income:,.2f}"])
    writer.writerow(["Total Expenses", f"N{total_expenses:,.2f}"])
    writer.writerow(["Deductible Expenses", f"N{deductible_expenses:,.2f}"])
    writer.writerow(["Taxable Income", f"N{taxable_income:,.2f}"])
    writer.writerow(["Income Tax", f"N{income_tax:,.2f}"])
    writer.writerow(["VAT (7.5%)", f"N{vat:,.2f}"])
    writer.writerow(["TOTAL TAX OWED", f"N{income_tax + vat:,.2f}"])
    writer.writerow([])
    writer.writerow(["INCOME BREAKDOWN"])
    for cat, amount in income_by_category.items():
        writer.writerow([cat, f"N{amount:,.2f}"])
    writer.writerow([])
    writer.writerow(["EXPENSE BREAKDOWN"])
    for cat, amount in expense_by_category.items():
        writer.writerow([cat, f"N{amount:,.2f}"])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=clearfileng_tax_report_{datetime.now().year}.csv"}
    )


@router.get("/reports/summary")
async def get_report_summary(period: str = "month", user: dict = Depends(get_current_user)):
    user_id = user["id"]
    now = datetime.now(timezone.utc)

    if period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "year":
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = now - timedelta(days=30)

    from datetime import timedelta
    transactions = await db.transactions.find({
        "user_id": user_id,
        "date": {"$gte": start_date.isoformat()}
    }, {"_id": 0}).to_list(10000)

    income_by_category = {}
    expense_by_category = {}
    for tx in transactions:
        cat = tx.get("category", "Other")
        if tx["type"] == "income":
            income_by_category[cat] = income_by_category.get(cat, 0) + tx["amount"]
        else:
            expense_by_category[cat] = expense_by_category.get(cat, 0) + tx["amount"]

    total_income = sum(income_by_category.values())
    total_expenses = sum(expense_by_category.values())

    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": total_income - total_expenses,
        "income_by_category": income_by_category,
        "expense_by_category": expense_by_category,
        "transaction_count": len(transactions)
    }
