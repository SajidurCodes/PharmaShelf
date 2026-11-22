import json

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
from app.modules.sales.repositories import SaleRepository


router = APIRouter(
    prefix="/imports",
    tags=["Imports"],
    dependencies=[Depends(require_admin)],
)
MAX_UPLOAD_BYTES = 2_000_000


async def read_upload(file: UploadFile, mapping: str) -> tuple[list[dict], list[dict]]:
    try:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
    finally:
        await file.close()

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Upload a workbook under 2 MB")

    try:
        columns = json.loads(mapping)
        if not isinstance(columns, dict) or not all(
            isinstance(value, str) for value in columns.values()
        ):
            raise ValueError("Mapping must contain sales fields paired with Excel column names")

        return await run_in_threadpool(read_sales_rows, content, columns)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/sales/preview")
async def preview_sales_upload(
    session: SessionDep,
    file: UploadFile = File(...),
    mapping: str = Form("{}"),
) -> dict:
    sales, errors = await read_upload(file, mapping)
    return await preview_sales_with_database(sales, errors, ImportRepository(session))


@router.post("/sales/confirm")
async def confirm_sales_upload(
    session: SessionDep,
    file: UploadFile = File(...),
    mapping: str = Form("{}"),
) -> dict:
    sales, errors = await read_upload(file, mapping)

    if errors:
        raise HTTPException(status_code=422, detail=errors)
    if not sales:
        raise HTTPException(status_code=422, detail="The workbook contains no sales")

    return await confirm_sales(sales, SaleRepository(session))