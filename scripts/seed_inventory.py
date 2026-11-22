import asyncio
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert

from app.db.session import SessionLocal, engine
from app.modules.inventory.models import Branch, StockBatch
from app.modules.medicines.models import Medicine


BRANCH_ID = UUID("00000000-0000-4000-8000-000000000001")
MEDICINE_ID = UUID("00000000-0000-4000-8000-000000000002")
FIRST_BATCH_ID = UUID("00000000-0000-4000-8000-000000000003")
SECOND_BATCH_ID = UUID("00000000-0000-4000-8000-000000000004")


async def seed_inventory() -> None:
    today = date.today()

    branch = {
        "id": BRANCH_ID,
        "code": "DEMO-01",
        "name": "Demo Pharmacy — Main Branch",
    }
    medicine = {
        "id": MEDICINE_ID,
        "sku": "DEMO-PARA-500",
        "name": "Demo Paracetamol 500",
        "generic_name": "Paracetamol",
        "strength": "500 mg",
        "dosage_form": "Tablet",
    }
    batches = [
        {
            "id": FIRST_BATCH_ID,
            "medicine_id": MEDICINE_ID,
            "branch_id": BRANCH_ID,
            "lot_number": "DEMO-LOT-A",
            "received_on": today - timedelta(days=30),
            "expires_on": today + timedelta(days=14),
            "quantity_received": 50,
            "quantity_remaining": 20,
            "unit_cost": Decimal("3.50"),
        },
        {
            "id": SECOND_BATCH_ID,
            "medicine_id": MEDICINE_ID,
            "branch_id": BRANCH_ID,
            "lot_number": "DEMO-LOT-B",
            "received_on": today - timedelta(days=5),
            "expires_on": today + timedelta(days=90),
            "quantity_received": 30,
            "quantity_remaining": 30,
            "unit_cost": Decimal("4.00"),
        },
    ]

    try:
        async with SessionLocal.begin() as session:
            await session.execute(
                insert(Branch).values(branch).on_conflict_do_nothing(
                    index_elements=[Branch.id]
                )
            )
            await session.execute(
                insert(Medicine).values(medicine).on_conflict_do_nothing(
                    index_elements=[Medicine.id]
                )
            )
            await session.execute(
                insert(StockBatch).values(batches).on_conflict_do_nothing(
                    index_elements=[StockBatch.id]
                )
            )
    finally:
        await engine.dispose()

    print("Demo inventory seed complete.")


if __name__ == "__main__":
    asyncio.run(seed_inventory())