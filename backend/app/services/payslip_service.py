"""Payslip PDF generation service — Phase 3 (Req 16.1, 16.2)."""

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_payslip_pdf(
    employee_full_name: str,
    designation_name: str | None,
    department_name: str | None,
    month: int,
    year: int,
    base_salary: float,
    absent_deductions: float,
    half_day_deductions: float,
    late_deductions: float,
    leave_deductions: float,
    overtime_pay: float,
    net_salary: float,
    generated_date: date | None = None,
) -> bytes:
    """Build a payslip PDF and return raw bytes.

    Satisfies Req 16.1: includes employee full name, designation name,
    department name, month/year label, base salary, itemised deductions
    (absent, half-day, late, leave), overtime pay, net salary, and
    generation date.
    """
    if generated_date is None:
        generated_date = date.today()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # ── Title ──────────────────────────────────────────────────────────────
    elements.append(Paragraph("<b>PAYSLIP</b>", styles["Title"]))
    elements.append(Spacer(1, 6 * mm))

    # ── Employee info table ────────────────────────────────────────────────
    month_label = date(year, month, 1).strftime("%B %Y")
    info_data = [
        ["Employee Name:", employee_full_name],
        ["Designation:", designation_name or "—"],
        ["Department:", department_name or "—"],
        ["Pay Period:", month_label],
        ["Generated On:", generated_date.strftime("%d %b %Y")],
    ]
    info_table = Table(info_data, colWidths=[45 * mm, 120 * mm])
    info_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    elements.append(info_table)
    elements.append(Spacer(1, 8 * mm))

    # ── Earnings & deductions table ────────────────────────────────────────
    def fmt(amount: float) -> str:
        return f"{amount:,.2f}"

    pay_data = [
        ["Description", "Amount (₹)"],
        ["Base Salary", fmt(base_salary)],
        ["", ""],
        ["Deductions", ""],
        ["  Absent Deductions", fmt(absent_deductions)],
        ["  Half-Day Deductions", fmt(half_day_deductions)],
        ["  Late Deductions", fmt(late_deductions)],
        ["  Leave Deductions", fmt(leave_deductions)],
        ["", ""],
        ["Overtime Pay", fmt(overtime_pay)],
        ["", ""],
        ["NET SALARY", fmt(net_salary)],
    ]

    col_w = [120 * mm, 45 * mm]
    pay_table = Table(pay_data, colWidths=col_w)
    pay_table.setStyle(
        TableStyle([
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            # Deductions header row
            ("FONTNAME", (0, 3), (0, 3), "Helvetica-Bold"),
            # Net salary row
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ecf0f1")),
            ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#2c3e50")),
        ])
    )
    elements.append(pay_table)
    elements.append(Spacer(1, 10 * mm))
    elements.append(
        Paragraph(
            "<i>This is a computer-generated payslip and does not require a signature.</i>",
            styles["Italic"],
        )
    )

    doc.build(elements)
    return buf.getvalue()
