from decimal import Decimal

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.imports.services import read_workbook_rows
from app.modules.inventory.models import Branch, StockBatch
from app.modules.inventory.repositories import InventoryRepository
from app.modules.inventory.schemas import StockReceiptCreate
from app.modules.medicines.models import Medicine






STOCK_COLUMNS = (
    "id",
    "branch_code",
    "sku",
    "lot_number",
    "received_on",
    "expires_on",
    "quantity_received",
    "unit_cost",
)




def parse_stock_row(raw: dict) -> dict:

    try:

        return StockReceiptCreate.model_validate(raw).model_dump()
    
    except ValidationError as exc:

        messages = []
        for error in exc.errors():
            field = ".".join(str(part) for part in error["loc"]) or "delivery"
            messages.append(f"{field}: {error['msg']}")
        raise ValueError("; ".join(messages)) from exc




def read_stock_rows(content: bytes,mapping: dict[str, str] | None = None,) -> tuple[list[dict], list[dict]]:

    return read_workbook_rows(
        content,
        mapping,
        sheet_name="Stock",
        columns=STOCK_COLUMNS,
        parse_row=parse_stock_row,
        id_field="id",
    )




async def preview_stock(rows: list[dict],errors: list[dict],session: AsyncSession,) -> dict:


    issues = errors.copy()
    preview = []
    valid = 0
    skipped = 0
    units = 0
    cost = Decimal("0.00")



    if rows:


        branch_query = select(Branch.code, Branch.id).where(
            Branch.code.in_({row["branch_code"] for row in rows})
        )

        medicine_query = select(Medicine.sku, Medicine.id).where(
            Medicine.sku.in_({row["sku"] for row in rows})
        )

        batch_query = select(StockBatch).where(
            StockBatch.id.in_({row["id"] for row in rows})
        )


        branches = dict((await session.execute(branch_query)).all())
        medicines = dict((await session.execute(medicine_query)).all())
        batches = {batch.id: batch for batch in await session.scalars(batch_query)}



        receipt_fields = ("lot_number", "received_on", "expires_on", "quantity_received", "unit_cost")



        for row in rows:

            branch_id = branches.get(row["branch_code"])

            medicine_id = medicines.get(row["sku"])

            batch = batches.get(row["id"])


            if branch_id is None:

                message = "Unknown branch_code"

            elif medicine_id is None:

                message = "Unknown sku"

            elif batch is not None:

                same_delivery = (batch.branch_id == branch_id and batch.medicine_id == medicine_id and all(getattr(batch, field) == row[field] for field in receipt_fields))




                if same_delivery:
                    skipped += 1
                    continue
                message = "This receipt ID was used for a different delivery"


            else:
                valid += 1
                units += row["quantity_received"]
                cost += row["quantity_received"] * row["unit_cost"]
                if len(preview) < 10:
                    preview.append(row)
                continue

            issues.append({"row": row["row"], "message": message})



    return {
        "valid_rows": valid,
        "invalid_rows": len(issues),
        "skipped_rows": skipped,
        "total_units": units,
        "cost_bdt": f"{cost:.2f}",
        "preview": preview,
        "errors": sorted(issues, key=lambda issue: issue["row"]),
    }




async def confirm_stock(rows: list[dict], session: AsyncSession) -> dict:
    repository = InventoryRepository(session)
    inserted = 0
    skipped = 0
    units = 0
    cost = Decimal("0.00")

    try:
        for row in sorted(rows, key=lambda item: item["id"]):
            delivery = StockReceiptCreate(**{field: row[field] for field in STOCK_COLUMNS})
            _, created = await repository.receive_stock(delivery)

            if created:
                inserted += 1
                units += delivery.quantity_received
                cost += delivery.quantity_received * delivery.unit_cost
            else:
                skipped += 1

        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return {
        "inserted_rows": inserted,
        "skipped_rows": skipped,
        "units_received": units,
        "cost_bdt": f"{cost:.2f}",
    }
