import json
from collections.abc import Callable

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.db.session import SessionDep
from app.modules.auth.dependencies import require_admin
from app.modules.imports.repositories import ImportRepository
from app.modules.imports.services import (
    confirm_sales,
    preview_sales_with_database,
    read_sales_rows,
)
from app.modules.imports.stock import confirm_stock, preview_stock, read_stock_rows
from app.modules.sales.repositories import SaleRepository


router = APIRouter(
    prefix="/imports",
    tags=["Imports"],
    dependencies=[Depends(require_admin)],
)

MAX_UPLOAD_BYTES = 2_000_000
RowReader = Callable[[bytes, dict[str, str]], tuple[list[dict], list[dict]]]


async def read_upload(
    file: UploadFile,
    mapping: str,
    reader: RowReader,
) -> tuple[list[dict], list[dict]]:
    try:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
    finally:
        await file.close()

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Upload a workbook of 2 MB or less")

    try:
        columns = json.loads(mapping)
        if not isinstance(columns, dict) or not all(
            isinstance(value, str) for value in columns.values()
        ):
            raise ValueError("Mapping must pair field names with Excel column names")

        return await run_in_threadpool(reader, content, columns)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def require_valid_rows(rows: list[dict], errors: list[dict], empty_message: str) -> None:
    if errors:
        raise HTTPException(status_code=422, detail=errors)
    if not rows:
        raise HTTPException(status_code=422, detail=empty_message)


@router.post("/sales/preview")
async def preview_sales_upload(
    session: SessionDep,
    file: UploadFile = File(...),
    mapping: str = Form("{}"),
) -> dict:
    rows, errors = await read_upload(file, mapping, read_sales_rows)
    return await preview_sales_with_database(rows, errors, ImportRepository(session))


@router.post("/sales/confirm")
async def confirm_sales_upload(
    session: SessionDep,
    file: UploadFile = File(...),
    mapping: str = Form("{}"),
) -> dict:
    rows, errors = await read_upload(file, mapping, read_sales_rows)
    require_valid_rows(rows, errors, "The workbook contains no sales")
    return await confirm_sales(rows, SaleRepository(session))


@router.post("/stock/preview")
async def preview_stock_upload(
    session: SessionDep,
    file: UploadFile = File(...),
    mapping: str = Form("{}"),
) -> dict:
    rows, errors = await read_upload(file, mapping, read_stock_rows)
    return await preview_stock(rows, errors, session)


@router.post("/stock/confirm")
async def confirm_stock_upload(
    session: SessionDep,
    file: UploadFile = File(...),
    mapping: str = Form("{}"),
) -> dict:
    rows, errors = await read_upload(file, mapping, read_stock_rows)
    require_valid_rows(rows, errors, "The workbook contains no stock rows")
    return await confirm_stock(rows, session)