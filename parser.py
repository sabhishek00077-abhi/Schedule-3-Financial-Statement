"""Robust Multi-Format Trial Balance Parser for Excel (.xlsx/.xls) and CSV formats."""
import os
import io
import csv
import re
import openpyxl
import pandas as pd
from typing import List, Tuple, Dict, Any
from .models import RawLedgerItem, ICAIGroup
from .classifier import classify_ledger

# Standard balanced sample trial balance
SAMPLE_TB_CSV = """Detailed Trial Balance Template
Account,Account Code,Debit (₹),Credit (₹)
ASSETS,,,
Cash at Bank,1010,250000,
Petty Cash,1020,15000,
Accounts Receivable,1030,180000,
Inventory,1040,320000,
Prepaid Expenses,1050,25000,
Equipment,1060,500000,
Accumulated Depreciation - Equipment,1061,,80000
Building,1070,1000000,
Accumulated Depreciation - Building,1071,,150000
LIABILITIES,,,
Accounts Payable,2010,,145000
Salaries Payable,2020,,35000
Interest Payable,2030,,8000
Short-term Loan,2040,,100000
Long-term Loan,2050,,400000
EQUITY,,,
Capital Stock,3010,,500000
Retained Earnings,3020,,694000
REVENUE,,,
Sales Revenue,4010,,850000
Service Revenue,4020,,125000
Interest Income,4030,,12000
EXPENSES,,,
Cost of Goods Sold,5010,425000,
Salaries Expense,5020,180000,
Rent Expense,5030,72000,
Depreciation Expense,5040,35000,
Utilities Expense,5050,28000,
Office Supplies Expense,5060,15000,
Insurance Expense,5070,24000,
Interest Expense,5080,18000,
Miscellaneous Expense,5090,12000,
,TOTAL,3099000,3099000
"""

def clean_amount(val: Any) -> float:
    """Cleans currency strings, commas, brackets into float."""
    if val is None or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val) if not pd.isna(val) else 0.0
    
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ["nan", "none", "-", "null"]:
        return 0.0
    
    # Handle accounting brackets: (100) -> -100
    is_neg = False
    if val_str.startswith("(") and val_str.endswith(")"):
        is_neg = True
        val_str = val_str[1:-1]
    elif val_str.startswith("-"):
        is_neg = True
        val_str = val_str[1:]
        
    # Remove currency symbols (₹, $, Rs.), commas, whitespace
    cleaned = re.sub(r"[^\d.]", "", val_str)
    try:
        amt = float(cleaned) if cleaned else 0.0
        return -amt if is_neg else amt
    except ValueError:
        return 0.0

def parse_trial_balance_rows(raw_rows: List[List[Any]]) -> Tuple[List[RawLedgerItem], Dict[str, Any]]:
    """Identifies header row, column positions, and extracts valid ledger rows."""
    if not raw_rows:
        return [], {"error": "Empty file provided"}
        
    # Step 1: Detect header row
    header_idx = -1
    account_col = -1
    code_col = -1
    debit_col = -1
    credit_col = -1
    group_col = -1
    
    for idx, row in enumerate(raw_rows[:15]):
        if not row:
            continue
        row_str = [str(c).lower().strip() if c is not None else "" for c in row]
        
        has_debit = any("debit" in c or "dr" == c or "dr." in c or "debit(₹)" in c for c in row_str)
        has_credit = any("credit" in c or "cr" == c or "cr." in c or "credit(₹)" in c for c in row_str)
        has_account = any("account" in c or "particular" in c or "ledger" in c or "head" in c or "name" in c or "description" in c for c in row_str)
        
        if (has_debit and has_credit) or (has_account and (has_debit or has_credit)):
            header_idx = idx
            for c_idx, val in enumerate(row_str):
                if any(k in val for k in ["account code", "code", "ac code", "ledger code"]):
                    code_col = c_idx
                elif any(k in val for k in ["account", "particular", "ledger", "head", "name", "description"]) and account_col == -1:
                    account_col = c_idx
                elif any(k in val for k in ["debit", "dr", "dr."]) and debit_col == -1:
                    debit_col = c_idx
                elif any(k in val for k in ["credit", "cr", "cr."]) and credit_col == -1:
                    credit_col = c_idx
                elif any(k in val for k in ["group", "schedule", "category", "parent"]) and group_col == -1:
                    group_col = c_idx
            break
            
    if header_idx == -1 or account_col == -1 or debit_col == -1:
        # Fallback to column index guess
        header_idx = 0
        account_col = 0
        debit_col = 2 if len(raw_rows[0]) > 2 else 1
        credit_col = 3 if len(raw_rows[0]) > 3 else (2 if len(raw_rows[0]) > 2 else 1)
        
    ledgers: List[RawLedgerItem] = []
    total_dr = 0.0
    total_cr = 0.0
    current_section = ""
    
    for row_idx in range(header_idx + 1, len(raw_rows)):
        row = raw_rows[row_idx]
        if not row or all(c is None or str(c).strip() == "" for c in row):
            continue
            
        acc_val = str(row[account_col]).strip() if account_col < len(row) and row[account_col] is not None else ""
        
        if acc_val.upper() in ["ASSETS", "LIABILITIES", "EQUITY", "REVENUE", "EXPENSES", "INCOME"]:
            current_section = acc_val.title()
            continue
            
        if any(k in acc_val.lower() for k in ["total", "grand total", "net total"]) or (code_col != -1 and code_col < len(row) and "total" in str(row[code_col]).lower()):
            continue
            
        code_val = str(row[code_col]).strip() if code_col != -1 and code_col < len(row) and row[code_col] is not None else ""
        dr_val = clean_amount(row[debit_col]) if debit_col < len(row) else 0.0
        cr_val = clean_amount(row[credit_col]) if credit_col < len(row) else 0.0
        orig_grp = str(row[group_col]).strip() if group_col != -1 and group_col < len(row) and row[group_col] is not None else current_section
        
        if not acc_val and dr_val == 0.0 and cr_val == 0.0:
            continue
            
        if not acc_val and (dr_val > 0 or cr_val > 0):
            acc_val = f"Ledger {row_idx}"
            
        assigned_group, conf = classify_ledger(acc_val, orig_grp, dr_val, cr_val)
        
        item = RawLedgerItem(
            id=f"leg_{row_idx}_{len(ledgers)}",
            name=acc_val,
            code=code_val,
            debit=dr_val,
            credit=cr_val,
            original_group=orig_grp,
            assigned_group=assigned_group,
            confidence=conf
        )
        ledgers.append(item)
        total_dr += dr_val
        total_cr += cr_val
        
    diff = round(total_dr - total_cr, 2)
    meta = {
        "total_ledgers": len(ledgers),
        "total_debit": round(total_dr, 2),
        "total_credit": round(total_cr, 2),
        "difference": diff,
        "is_balanced": abs(diff) < 0.01,
        "unmapped_count": sum(1 for l in ledgers if l.assigned_group == ICAIGroup.UNMAPPED)
    }
    return ledgers, meta

def parse_file_bytes(content: bytes, filename: str) -> Tuple[List[RawLedgerItem], Dict[str, Any]]:
    """
    Parses Excel or CSV bytes into ledger items.
    Handles:
    - Native .xlsx Excel binary (openpyxl)
    - Legacy .xls Excel binary (pandas / xlrd)
    - CSV plain text with UTF-8, UTF-8-BOM, CP1252, Latin1
    - CSV files saved with .xlsx extension
    """
    # Check if binary content starts with standard PK zip signature (native xlsx)
    is_zip = content.startswith(b"PK\x03\x04")
    
    if is_zip:
        try:
            wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
            sheet = wb.active
            raw_rows = list(sheet.iter_rows(values_only=True))
            if raw_rows:
                return parse_trial_balance_rows(raw_rows)
        except Exception:
            pass

    # Try parsing as CSV text (handles CSV, TSV, and CSV-named-as-.xlsx)
    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin1"]:
        try:
            text = content.decode(encoding)
            # Detect delimiter
            delimiter = ","
            if "\t" in text and text.count("\t") > text.count(","):
                delimiter = "\t"
            elif ";" in text and text.count(";") > text.count(","):
                delimiter = ";"
                
            reader = csv.reader(io.StringIO(text), delimiter=delimiter)
            raw_rows = list(reader)
            if raw_rows and any(len(r) > 1 for r in raw_rows[:10]):
                return parse_trial_balance_rows(raw_rows)
        except Exception:
            continue

    # Fallback to pandas excel reader for legacy .xls formats
    try:
        df = pd.read_excel(io.BytesIO(content))
        raw_rows = [df.columns.tolist()] + df.values.tolist()
        return parse_trial_balance_rows(raw_rows)
    except Exception as e:
        return [], {"error": f"Failed to parse file: {str(e)}"}

def load_sample_trial_balance() -> Tuple[List[RawLedgerItem], Dict[str, Any]]:
    """Loads the pre-configured sample trial balance dataset."""
    return parse_file_bytes(SAMPLE_TB_CSV.encode("utf-8"), "sample_trial_balance.csv")
