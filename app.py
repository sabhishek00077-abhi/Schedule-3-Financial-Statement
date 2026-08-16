"""FastAPI Application Server for Sched 3 Enterprise (Big 4 Edition)."""
import os
import io
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.models import RawLedgerItem, ICAIGroup, ICAI_GROUP_LABELS, EntityInfo
from backend.parser import parse_file_bytes, load_sample_trial_balance
from backend.statement_engine import generate_financial_statements
from backend.excel_exporter import create_excel_workbook

app = FastAPI(title="Sched 3 Enterprise — Big 4 ICAI Non-Corporate Financial & Audit Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EntityModel(BaseModel):
    name: str = "Shree Balaji Enterprises"
    entity_type: str = "Partnership Firm"
    financial_year: str = "2025-2026"
    as_on_date: str = "31st March 2026"
    currency_symbol: str = "₹"
    round_off: str = "Actuals"

class LedgerUpdateItem(BaseModel):
    id: str
    name: str
    code: Optional[str] = ""
    debit: float = 0.0
    credit: float = 0.0
    original_group: Optional[str] = ""
    assigned_group: str
    confidence: Optional[float] = 1.0

class AJEModel(BaseModel):
    id: Optional[str] = ""
    type: Optional[str] = "AJE"
    debit_account: str
    credit_account: str
    amount: float
    reason: Optional[str] = "Year-End Audit Adjustment"

class CalculateRequest(BaseModel):
    ledgers: List[LedgerUpdateItem]
    entity: EntityModel
    adjustments: Optional[List[AJEModel]] = None

@app.get("/api/groups")
async def get_icai_groups():
    """Returns the list of all ICAI Schedule III Non-Corporate groups with human labels."""
    return [
        {"key": g.value, "label": ICAI_GROUP_LABELS.get(g, g.value)}
        for g in ICAIGroup if g != ICAIGroup.UNMAPPED
    ] + [{"key": ICAIGroup.UNMAPPED.value, "label": ICAI_GROUP_LABELS[ICAIGroup.UNMAPPED]}]

@app.get("/api/sample-tb")
async def get_sample_tb():
    """Returns the built-in sample trial balance."""
    ledgers, meta = load_sample_trial_balance()
    return {
        "ledgers": [
            {
                "id": l.id,
                "name": l.name,
                "code": l.code,
                "debit": l.debit,
                "credit": l.credit,
                "original_group": l.original_group,
                "assigned_group": l.assigned_group.value,
                "confidence": l.confidence
            }
            for l in ledgers
        ],
        "meta": meta
    }

@app.post("/api/upload-tb")
async def upload_trial_balance(file: UploadFile = File(...)):
    """Uploads and parses an Excel (.xlsx/.xls) or CSV trial balance."""
    content = await file.read()
    filename = file.filename or "trial_balance.xlsx"
    ledgers, meta = parse_file_bytes(content, filename)
    
    if "error" in meta:
        raise HTTPException(status_code=400, detail=meta["error"])
        
    return {
        "filename": filename,
        "ledgers": [
            {
                "id": l.id,
                "name": l.name,
                "code": l.code,
                "debit": l.debit,
                "credit": l.credit,
                "original_group": l.original_group,
                "assigned_group": l.assigned_group.value,
                "confidence": l.confidence
            }
            for l in ledgers
        ],
        "meta": meta
    }

@app.post("/api/generate-statements")
async def compute_statements(payload: CalculateRequest):
    """Computes Balance Sheet, P&L, CFS, Notes, Ratios, PPE, Aging, and Audit Reports."""
    raw_ledgers = [
        RawLedgerItem(
            id=it.id,
            name=it.name,
            code=it.code or "",
            debit=it.debit,
            credit=it.credit,
            original_group=it.original_group or "",
            assigned_group=ICAIGroup(it.assigned_group) if it.assigned_group in [g.value for g in ICAIGroup] else ICAIGroup.UNMAPPED,
            confidence=it.confidence or 1.0
        )
        for it in payload.ledgers
    ]
    entity = EntityInfo(
        name=payload.entity.name,
        entity_type=payload.entity.entity_type,
        financial_year=payload.entity.financial_year,
        as_on_date=payload.entity.as_on_date,
        currency_symbol=payload.entity.currency_symbol,
        round_off=payload.entity.round_off
    )
    
    adj_dicts = [a.model_dump() for a in payload.adjustments] if payload.adjustments else []
    result = generate_financial_statements(raw_ledgers, entity, adjustments=adj_dicts)
    return result

@app.post("/api/export-excel")
async def export_excel(payload: CalculateRequest):
    """Generates and streams back a Big 4 styled multi-tab Excel workbook (.xlsx)."""
    raw_ledgers = [
        RawLedgerItem(
            id=it.id,
            name=it.name,
            code=it.code or "",
            debit=it.debit,
            credit=it.credit,
            original_group=it.original_group or "",
            assigned_group=ICAIGroup(it.assigned_group) if it.assigned_group in [g.value for g in ICAIGroup] else ICAIGroup.UNMAPPED,
            confidence=it.confidence or 1.0
        )
        for it in payload.ledgers
    ]
    entity = EntityInfo(
        name=payload.entity.name,
        entity_type=payload.entity.entity_type,
        financial_year=payload.entity.financial_year,
        as_on_date=payload.entity.as_on_date,
        currency_symbol=payload.entity.currency_symbol,
        round_off=payload.entity.round_off
    )
    
    adj_dicts = [a.model_dump() for a in payload.adjustments] if payload.adjustments else []
    result = generate_financial_statements(raw_ledgers, entity, adjustments=adj_dicts)
    excel_buf = create_excel_workbook(result)
    
    safe_name = entity.name.replace(" ", "_")
    filename = f"{safe_name}_Big4_Financial_Statements_{entity.financial_year}.xlsx"
    
    return StreamingResponse(
        excel_buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_index():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Sched 3 Enterprise API running."}
