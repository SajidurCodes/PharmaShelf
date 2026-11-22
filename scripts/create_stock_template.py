from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "app/frontend/templates/stock-template.xlsx"
)


def main() -> None:
    book = Workbook()
    sheet = book.active
    sheet.title = "Stock"

    sheet.append([
        "id", "branch_code", "sku", "lot_number", "received_on",
        "expires_on", "quantity_received", "unit_cost",
    ])
    sheet.append([
        "00000000-0000-4000-8000-000000000201",
        "DEMO-01", "DEMO-PARA-500", "DEMO-LOT-B",
        date(2026, 11, 22), date(2027, 11, 22), 24, 3.50,
    ])

    for cell in sheet[1]:
        cell.fill = PatternFill(fill_type="solid", fgColor="174535")
        cell.font = Font(color="FFFFFF", bold=True)
    for col, width in zip("ABCDEFGH", [40, 17, 24, 23, 17, 17, 22, 17]):
        sheet.column_dimensions[col].width = width
    for cell in ("E2", "F2"):
        sheet[cell].number_format = "yyyy-mm-dd"
    sheet["H2"].number_format = "0.00"
    sheet.freeze_panes = "A2"

    guide = book.create_sheet("Instructions")
    for line in [
        "Use one row per incoming delivery of one medicine lot.",
        "The example row is demo data. Replace it with your delivery records.",
        "Use a unique UUID for each delivery and keep it when retrying that delivery.",
        "Use an existing branch code and medicine SKU.",
        "Quantity received is the number of units delivered. Unit cost is in BDT.",
    ]:
        guide.append([line])
    guide.column_dimensions["A"].width = 90

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    book.save(OUTPUT)
    book.close()
    print(f"Created {OUTPUT.name}")


if __name__ == "__main__":
    main()