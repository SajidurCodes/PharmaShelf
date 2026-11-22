import asyncio

from app.db.session import SessionLocal
from app.modules.almanac.repositories import AlmanacRepository
from app.modules.almanac.schemas import AlmanacEntryCreate


ENTRIES = [
    AlmanacEntryCreate(
        slug="sales-stopped-at-one-branch",
        title="Why did a medicine suddenly stop selling?",
        topic="demand",
        content=(
            "Start with the last day the branch recorded a sale. Check which lots "
            "were still usable that day and when the next delivery arrived. A gap "
            "between the last sale and the next receipt is a reason to investigate "
            "a stock-out. Ask the pharmacist whether customers requested the item "
            "during the gap. A sales ledger records purchases; it cannot count "
            "customers who left empty-handed."
        ),
        source_note=(
            "PharmaShelf operational guide. Check the branch sales ledger, batch "
            "receipt dates, expiry dates, and the pharmacist’s counter observations."
        ),
    ),
    AlmanacEntryCreate(
        slug="reading-a-weekly-demand-spike",
        title="What does a weekly demand spike mean?",
        topic="demand",
        content=(
            "Suppose a branch usually sells four units a week and sold twelve in "
            "the last seven completed days. That is three times its baseline. "
            "Check whether the twelve units came from several sales or one large "
            "purchase, then check the next supplier delivery date. The alert helps "
            "the owner decide when to review stock. Sales alone cannot establish "
            "a medical or seasonal cause."
        ),
        source_note=(
            "PharmaShelf demand-spike report. The baseline is the weekly average "
            "of the preceding 28 days. The quantities in this entry are illustrative."
        ),
    ),
    AlmanacEntryCreate(
        slug="reading-days-of-stock",
        title="How should I use the days-left estimate?",
        topic="reorder",
        content=(
            "If a branch sold thirty units in thirty days and has six usable units "
            "left, the recent pace suggests about six days of cover. Compare that "
            "with the supplier’s delivery time. A delivery due tomorrow and one "
            "due next week call for different decisions. For a recently introduced "
            "medicine, review the receipt date: a full thirty-day average can make "
            "a few days of brisk sales look slower than they are."
        ),
        source_note=(
            "PharmaShelf stock and reorder report. Estimated days left equals "
            "usable units multiplied by 30, divided by units sold in the last "
            "30 completed days. The example quantities are illustrative."
        ),
    ),
    AlmanacEntryCreate(
        slug="prioritizing-expiring-lots",
        title="Which expiring lot deserves attention first?",
        topic="expiry",
        content=(
            "Two lots of the same medicine can have different expiry dates and "
            "different amounts of money at risk. Review each lot separately. "
            "Multiply its remaining units by its unit cost, then compare its expiry "
            "date with the branch’s recent sales pace. If a slow-moving lot is "
            "unlikely to clear in time, contact the supplier early to ask about "
            "return or exchange terms."
        ),
        source_note=(
            "PharmaShelf expiry-rescue report and batch ledger. Value at risk uses "
            "remaining quantity and recorded unit cost. Return or exchange eligibility "
            "depends on the supplier’s terms."
        ),
    ),
]


async def seed_almanac() -> None:
    async with SessionLocal() as session:
        repository = AlmanacRepository(session)
        inserted = 0

        async with session.begin():
            for data in ENTRIES:
                entry = await repository.create(data)
                if entry is not None:
                    inserted += 1

        print(f"Almanac entries added: {inserted}; already present: {len(ENTRIES) - inserted}")


if __name__ == "__main__":
    asyncio.run(seed_almanac())