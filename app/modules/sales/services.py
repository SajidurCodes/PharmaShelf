
from zoneinfo import ZoneInfo
from datetime import datetime, time, timedelta, timezone
from app.core.exceptions.errors import ConflictError, NotFoundError
from app.modules.sales.repositories import SaleRepository
from app.modules.sales.schemas import BestSellerFilters, BestSellerRead, SaleCreate, SaleRead



class SaleService:
    def __init__(self, repository: SaleRepository):
        self.repository = repository

    async def record(self, data: SaleCreate) -> tuple[SaleRead, bool]:
        session = self.repository.session
        try:
            result = await self.record_in_transaction(data)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise

    async def record_in_transaction(
        self,
        data: SaleCreate,
        *,
        sold_at: datetime | None = None,
    ) -> tuple[SaleRead, bool]:
        """Record one sale. The caller owns the commit or rollback."""
        batch = await self.repository.lock_batch(data.batch_id)
        if batch is None:
            raise NotFoundError("Stock batch was not found")

        sale_time = sold_at if sold_at is not None else datetime.now(timezone.utc)
        sale = await self.repository.insert_once(data, sale_time)

        if sale is None:
            existing = await self.repository.get_by_id(data.id)
            if (
                existing is None
                or existing.batch_id != data.batch_id
                or existing.quantity != data.quantity
                or existing.unit_sale_price != data.unit_sale_price
                or (sold_at is not None and existing.sold_at != sale_time)
            ):
                raise ConflictError("This sale ID was used for a different sale")

            return SaleRead.model_validate(existing), False

        sale_day = sale_time.astimezone(ZoneInfo("Asia/Dhaka")).date()
        if batch.received_on > sale_day or batch.expires_on <= sale_day:
            raise ConflictError("This batch was unavailable on the sale date")

        if batch.quantity_remaining < data.quantity:
            raise ConflictError("Insufficient stock in this batch")

        batch.quantity_remaining -= data.quantity
        return SaleRead.model_validate(sale), True

    async def best_sellers(self, filters: BestSellerFilters) -> list[BestSellerRead]:
        dhaka = ZoneInfo("Asia/Dhaka")
        start = datetime.combine(filters.start_date, time.min, tzinfo=dhaka)
        next_day = filters.end_date + timedelta(days=1)
        stop = datetime.combine(next_day, time.min, tzinfo=dhaka)

        return await self.repository.best_sellers(filters, start, stop)