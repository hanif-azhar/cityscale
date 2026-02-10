from __future__ import annotations

from io import BytesIO
from typing import Any, Mapping

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def _figure_to_png_bytes(figure: Any, width: int = 1200, height: int = 650) -> bytes | None:
    if figure is None:
        return None
    try:
        return figure.to_image(format="png", width=width, height=height, scale=2)
    except Exception:
        return None


def export_excel_report(
    base_activity: pd.DataFrame,
    factors: pd.DataFrame,
    sector_results: pd.DataFrame,
    forecast: pd.DataFrame,
    charts: Mapping[str, Any] | None = None,
) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        base_activity.to_excel(writer, sheet_name="BaseActivity", index=False)
        factors.to_excel(writer, sheet_name="EmissionFactors", index=False)
        sector_results.to_excel(writer, sheet_name="BaseResults", index=False)
        forecast.to_excel(writer, sheet_name="ScenarioForecast", index=False)

        if charts:
            workbook = writer.book
            chart_sheet = workbook.add_worksheet("Charts")
            writer.sheets["Charts"] = chart_sheet
            chart_sheet.set_column("A:A", 55)

            row = 0
            for name, figure in charts.items():
                label = name.replace("_", " ").title()
                chart_sheet.write(row, 0, label)
                row += 1

                png_bytes = _figure_to_png_bytes(figure, width=1100, height=520)
                if png_bytes:
                    chart_sheet.insert_image(
                        row,
                        0,
                        f"{name}.png",
                        {"image_data": BytesIO(png_bytes), "x_scale": 0.62, "y_scale": 0.62},
                    )
                else:
                    chart_sheet.write(row, 0, f"Chart image unavailable for '{name}'. Install kaleido.")

                row += 24
    buffer.seek(0)
    return buffer.getvalue()


def export_pdf_report(
    city_name: str,
    summary: dict,
    sector_results: pd.DataFrame,
    forecast: pd.DataFrame,
    charts: Mapping[str, Any] | None = None,
) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, f"CityScale Report: {city_name}")
    y -= 24

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Total CO2e: {summary['total_co2e']:.2f}")
    y -= 16
    c.drawString(40, y, f"Per capita CO2e: {summary['per_capita_co2e']:.6f}")
    y -= 16
    c.drawString(40, y, f"Per GDP CO2e: {summary['per_gdp_co2e']:.8f}")
    y -= 24

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Sector Emissions")
    y -= 16
    c.setFont("Helvetica", 9)
    for _, row in sector_results.iterrows():
        c.drawString(40, y, f"{row['sector']}: {row['co2e']:.2f}")
        y -= 14
        if y < 80:
            c.showPage()
            y = height - 40

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Scenario Highlights")
    y -= 16
    c.setFont("Helvetica", 9)
    latest = forecast.sort_values("year").groupby("scenario").tail(1)
    for _, row in latest.iterrows():
        c.drawString(
            40,
            y,
            f"{int(row['year'])} {row['scenario']}: {row['total_co2e']:.2f} ({row['change_vs_baseline_pct']:.2f}% vs baseline)",
        )
        y -= 14
        if y < 80:
            c.showPage()
            y = height - 40

    if charts:
        c.showPage()
        y = height - 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Charts")
        y -= 20
        chart_width = width - 80
        chart_height = 220

        for name, figure in charts.items():
            if y - chart_height < 60:
                c.showPage()
                y = height - 40

            c.setFont("Helvetica-Bold", 10)
            c.drawString(40, y, name.replace("_", " ").title())
            y -= 14

            png_bytes = _figure_to_png_bytes(figure, width=1200, height=550)
            if png_bytes:
                image = ImageReader(BytesIO(png_bytes))
                c.drawImage(
                    image,
                    40,
                    y - chart_height,
                    width=chart_width,
                    height=chart_height,
                    preserveAspectRatio=True,
                    anchor="n",
                )
            else:
                c.setFont("Helvetica-Oblique", 9)
                c.drawString(40, y - 10, f"Chart image unavailable for '{name}'. Install kaleido.")

            y -= chart_height + 20

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
