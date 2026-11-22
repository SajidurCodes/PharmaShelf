from collections.abc import Callable
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from uuid import UUID
from zipfile import BadZipFile, ZipFile
from zoneinfo import ZoneInfo

from openpyxl import load_workbook

from app.modules.imports.repositories import ImportRepository
from app.modules.sales.repositories import SaleRepository
from app.modules.sales.schemas import SaleCreate
from app.modules.sales.services import SaleService


SALES_COLUMNS = ("sale_id", "batch_id", "sold_at", "quantity", "unit_sale_price")
MAX_ROWS = 1000
MAX_COLUMNS = 100
MAX_EXPANDED_BYTES = 20_000_000


def resolve_columns(
    headers: list,
    mapping: dict[str, str],
    columns: tuple[str, ...] = SALES_COLUMNS,
) -> dict[str, int]:
    """Match each required field to exactly one Excel column."""
    unknown = set(mapping) - set(columns)
    if unknown:
        raise ValueError(f"Unknown import field: {', '.join(sorted(unknown))}")

    normalized = [str(value or "").strip().casefold() for value in headers]
    positions = {}

    for field in columns:
        source = mapping.get(field, field).strip().casefold()

        if not source or normalized.count(source) != 1:
            raise ValueError(f"Choose one unique Excel column for {field}")

        index = normalized.index(source)
        if index in positions.values():
            raise ValueError(f"The Excel column '{headers[index]}' is mapped twice")

        positions[field] = index

    return positions


def parse_sale(row: dict) -> dict:
    """Validate one sales row and normalize its values."""
    ids = {}
    for field in ("sale_id", "batch_id"):
        try:
            ids[field] = str(UUID(str(row[field]).strip()))
        except ValueError:
            raise ValueError(f"{field} must be a valid UUID") from None

    sold_at = row["sold_at"]
    if not isinstance(sold_at, datetime):
        try:
            sold_at = datetime.fromisoformat(str(sold_at).strip())
        except ValueError:
            raise ValueError(
                "sold_at must be an Excel date or an ISO date and time"
            ) from None

    try:
        quantity = Decimal(str(row["quantity"]))
    except InvalidOperation:
        raise ValueError("quantity must be a positive whole number") from None

    if (
        not quantity.is_finite()
        or quantity < 1
        or quantity > 2_147_483_647
        or quantity != quantity.to_integral_value()
    ):
        raise ValueError("quantity must be a whole number between 1 and 2147483647")

    try:
        price = Decimal(str(row["unit_sale_price"]))
    except InvalidOperation:
        raise ValueError("unit_sale_price must be a number in BDT") from None

    if (
        not price.is_finite()
        or price < 0
        or price > Decimal("9999999999.99")
        or price != price.quantize(Decimal("0.01"))
    ):
        raise ValueError(
            "unit_sale_price must be between 0 and 9999999999.99 "
            "and have at most two decimal places"
        )

    return {
        **ids,
        "sold_at": sold_at.isoformat(),
        "quantity": int(quantity),
        "unit_sale_price": price,
    }


def read_workbook_rows(
    content: bytes,
    mapping: dict[str, str] | None,
    *,
    sheet_name: str,
    columns: tuple[str, ...],
    parse_row: Callable[[dict], dict],
    id_field: str,
) -> tuple[list[dict], list[dict]]:
    """Read a sales or stock sheet and keep the original Excel row numbers."""
    try:
        with ZipFile(BytesIO(content)) as archive:
            expanded_size = sum(item.file_size for item in archive.infolist())
            if expanded_size > MAX_EXPANDED_BYTES:
                raise ValueError("The expanded workbook exceeds the 20 MB preview limit")

        workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
    except (BadZipFile, KeyError, OSError) as exc:
        raise ValueError("Upload a valid .xlsx workbook") from exc

    try:
        if sheet_name not in workbook.sheetnames:
            raise ValueError(f"The workbook needs a sheet named {sheet_name}")

        sheet = workbook[sheet_name]
        if sheet.max_column and sheet.max_column > MAX_COLUMNS:
            raise ValueError(
                f"The {sheet_name} sheet exceeds the {MAX_COLUMNS}-column preview limit"
            )

        rows = iter(sheet.values)
        headers = list(next(rows, ()))
        positions = resolve_columns(headers, mapping or {}, columns)

        records = []
        errors = []
        seen_ids = set()

        for row_number, values in enumerate(rows, start=2):
            if row_number > MAX_ROWS + 1:
                raise ValueError(f"Preview supports up to {MAX_ROWS} data rows per sheet")

            if all(value is None for value in values):
                continue

            raw = {
                field: values[index] if index < len(values) else None
                for field, index in positions.items()
            }

            try:
                record = parse_row(raw)
                record_id = record[id_field]
                if record_id in seen_ids:
                    raise ValueError(
                        f"{id_field} repeats an earlier valid row in this workbook"
                    )
            except ValueError as exc:
                errors.append({"row": row_number, "message": str(exc)})
                continue

            seen_ids.add(record_id)
            records.append({**record, "row": row_number})

        return records, errors
    finally:
        workbook.close()


def read_sales_rows(
    content: bytes,
    mapping: dict[str, str] | None = None,
) -> tuple[list[dict], list[dict]]:
    return read_workbook_rows(
        content,
        mapping,
        sheet_name="Sales",
        columns=SALES_COLUMNS,
        parse_row=parse_sale,
        id_field="sale_id",
    )


def build_preview(sales: list[dict], errors: list[dict]) -> dict:
    revenue = sum(
        (sale["quantity"] * sale["unit_sale_price"] for sale in sales),
        Decimal("0.00"),
    )

    return {
        "valid_rows": len(sales),
        "invalid_rows": len(errors),
        "total_units": sum(sale["quantity"] for sale in sales),
        "revenue_bdt": f"{revenue:.2f}",
        "preview": [
            {**sale, "unit_sale_price": f"{sale['unit_sale_price']:.2f}"}
            for sale in sales[:10]
        ],
        "errors": sorted(errors, key=lambda error: error["row"]),
    }


def preview_sales(content: bytes, mapping: dict[str, str] | None = None) -> dict:
    sales, errors = read_sales_rows(content, mapping)
    return build_preview(sales, errors)


async def preview_sales_with_database(
    sales: list[dict],
    errors: list[dict],
    repository: ImportRepository,
) -> dict:
    if not sales:
        return build_preview([], errors)

    batch_ids = {UUID(sale["batch_id"]) for sale in sales}
    sale_ids = {UUID(sale["sale_id"]) for sale in sales}

    known_batches = await repository.existing_batch_ids(batch_ids)
    recorded_sales = await repository.existing_sale_ids(sale_ids)

    valid_sales = []
    row_errors = errors.copy()

    for sale in sales:
        if UUID(sale["sale_id"]) in recorded_sales:
            message = "sale_id is already recorded"
        elif UUID(sale["batch_id"]) not in known_batches:
            message = "Unknown batch_id"
        else:
            valid_sales.append(sale)
            continue

        row_errors.append({"row": sale["row"], "message": message})

    return build_preview(valid_sales, row_errors)


async def confirm_sales(
    sales: list[dict],
    repository: SaleRepository,
) -> dict:
    service = SaleService(repository)
    dhaka = ZoneInfo("Asia/Dhaka")
    inserted = 0
    skipped = 0
    units_recorded = 0
    revenue_recorded = Decimal("0.00")

    # Take batch locks in a consistent order for overlapping uploads.
    ordered_sales = sorted(sales, key=lambda row: (row["batch_id"], row["sale_id"]))

    try:
        for row in ordered_sales:
            sold_at = datetime.fromisoformat(row["sold_at"])
            if sold_at.tzinfo is None:
                sold_at = sold_at.replace(tzinfo=dhaka)

            data = SaleCreate(
                id=UUID(row["sale_id"]),
                batch_id=UUID(row["batch_id"]),
                quantity=row["quantity"],
                unit_sale_price=row["unit_sale_price"],
            )

            _, created = await service.record_in_transaction(data, sold_at=sold_at)
            if created:
                inserted += 1
                units_recorded += data.quantity
                revenue_recorded += data.quantity * data.unit_sale_price
            else:
                skipped += 1

        await repository.session.commit()
    except Exception:
        await repository.session.rollback()
        raise

    return {
        "inserted_rows": inserted,
        "skipped_rows": skipped,
        "units_recorded": units_recorded,
        "revenue_recorded_bdt": f"{revenue_recorded:.2f}",
    }