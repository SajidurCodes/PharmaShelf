
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
            batch = await self.repository.lock_batch(data.batch_id)
            if batch is None:
                raise NotFoundError("Stock batch was not found")

            now = datetime.now(timezone.utc)
            sale = await self.repository.insert_once(data, now)
            created = sale is not None

            if created:
                today = now.astimezone(ZoneInfo("Asia/Dhaka")).date()

                if batch.received_on > today or batch.expires_on <= today:
                    raise ConflictError("This batch is unavailable for sale")

                if batch.quantity_remaining < data.quantity:
                    raise ConflictError("Insufficient stock in this batch")

                batch.quantity_remaining -= data.quantity
            else:
                sale = await self.repository.get_by_id(data.id)
                if (
                    sale is None
                    or sale.batch_id != data.batch_id
                    or sale.quantity != data.quantity
                    or sale.unit_sale_price != data.unit_sale_price
                ):
                    raise ConflictError("This sale ID was used for a different sale")

            result = SaleRead.model_validate(sale)
            await session.commit()
            return result, created

        except Exception:
            await session.rollback()
            raise

    async def best_sellers(self, filters: BestSellerFilters) -> list[BestSellerRead]:
        dhaka = ZoneInfo("Asia/Dhaka")
        start = datetime.combine(filters.start_date, time.min, tzinfo=dhaka)
        next_day = filters.end_date + timedelta(days=1)
        stop = datetime.combine(next_day, time.min, tzinfo=dhaka)

        return await self.repository.best_sellers(filters, start, stop)