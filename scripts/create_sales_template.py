from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_ROOT / "app" / "frontend" / "templates" / "sales-template.xlsx"


def main() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sales"

    sheet.append(["sale_id", "batch_id", "sold_at", "quantity", "unit_sale_price"])
    sheet.append([
        "00000000-0000-4000-8000-000000000101",
        "00000000-0000-4000-8000-000000000003",
        datetime(2026, 11, 22, 10, 30),
        2,
        5.00,
    ])

    for cell in sheet[1]:
        cell.fill = PatternFill(fill_type="solid", fgColor="174535")
        cell.font = Font(color="FFFFFF", bold=True)

    for column, width in {"A": 40, "B": 40, "C": 24, "D": 14, "E": 20}.items():
        sheet.column_dimensions[column].width = width

    sheet["C2"].number_format = "yyyy-mm-dd hh:mm"
    sheet["E2"].number_format = '"৳"#,##0.00'
    sheet.freeze_panes = "A2"

    guide = workbook.create_sheet("Instructions")
    for line in [
        "PharmaShelf sales import",
        "The Sales sheet contains one demo sale. Replace it with your own rows.",
        "Use one row per sale line. Each sale_id is a unique UUID for that line.",
        "Keep the same sale_id when uploading the same sale again.",
        "batch_id identifies the stock batch the units came from.",
        "Enter sold_at in Bangladesh local time.",
        "Quantity is a positive whole number. Unit sale price is in BDT.",
    ]:
        guide.append([line])
    guide.column_dimensions["A"].width = 90

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(OUTPUT)
    print(f"Created {OUTPUT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()