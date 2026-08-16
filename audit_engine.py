"""ICAI Non-Corporate Level Classification & Audit Adjustments (AJE) Engine."""
from typing import Dict, Any, List, Tuple
from .models import RawLedgerItem, ICAIGroup

def determine_icai_entity_level(turnover: float, borrowings: float, is_bank_or_fi: bool = False) -> Dict[str, Any]:
    """
    Determines ICAI Non-Corporate Entity Level (Level I, II, III, IV)
    as per ICAI Technical Guide and AS applicability criteria.
    Thresholds in INR:
    - Level I: Turnover > 50 Cr (500m) or Borrowings > 10 Cr (100m) or Bank/FI/Insurance
    - Level II: Turnover 10 Cr - 50 Cr (100m - 500m) or Borrowings 2 Cr - 10 Cr (20m - 100m)
    - Level III: Turnover 50 Lakhs - 10 Cr (5m - 100m) or Borrowings 10 Lakhs - 2 Cr (1m - 20m)
    - Level IV: Micro Non-Corporate Entities (Turnover < 50 Lakhs and Borrowings < 10 Lakhs)
    """
    if is_bank_or_fi or turnover >= 500000000.0 or borrowings >= 100000000.0:
        level = "Level I"
        category = "Large Non-Corporate Entity"
        exemptions = []
        cfs_mandatory = True
        desc = "Full Accounting Standards apply without disclosure exemptions."
    elif turnover >= 100000000.0 or borrowings >= 20000000.0:
        level = "Level II"
        category = "Medium Non-Corporate Entity (SME)"
        exemptions = ["AS 17 (Segment Reporting)", "AS 18 (Related Party partial)", "AS 28 (Impairment partial)"]
        cfs_mandatory = True
        desc = "Eligible for select disclosure relaxations under AS 17, 18, and 28."
    elif turnover >= 5000000.0 or borrowings >= 1000000.0:
        level = "Level III"
        category = "Small Non-Corporate Entity"
        exemptions = [
            "AS 3 (Cash Flow Statement is Optional)",
            "AS 17 (Segment Reporting exempt)",
            "AS 18 (Related Party Disclosures exempt)",
            "AS 24 (Discontinuing Operations exempt)"
        ]
        cfs_mandatory = False
        desc = "Eligible for major exemptions. Cash Flow Statement is optional."
    else:
        level = "Level IV"
        category = "Micro Non-Corporate Entity"
        exemptions = [
            "AS 3 (Cash Flow Statement is Exempt)",
            "AS 17 (Segment Reporting exempt)",
            "AS 18 (Related Party Disclosures exempt)",
            "AS 24 (Discontinuing Operations exempt)",
            "AS 28 (Impairment of Assets exempt)",
            "Simplified AS-15 Employee Benefits"
        ]
        cfs_mandatory = False
        desc = "Micro non-corporate enterprise with maximum AS reporting exemptions."

    return {
        "level": level,
        "category": category,
        "turnover": turnover,
        "borrowings": borrowings,
        "cfs_mandatory": cfs_mandatory,
        "exemptions": exemptions,
        "description": desc
    }

def apply_audit_adjustments(
    ledgers: List[RawLedgerItem],
    adjustments: List[Dict[str, Any]]
) -> Tuple[List[RawLedgerItem], Dict[str, Any]]:
    """
    Applies Year-End Adjusting Journal Entries (AJEs / RJEs) to the raw trial balance
    and produces an audited 3-column working paper schedule.
    """
    ledger_map = {l.id: l for l in ledgers}
    name_map = {l.name.lower().strip(): l for l in ledgers}
    
    total_adj_dr = 0.0
    total_adj_cr = 0.0
    applied_list = []

    for aje in adjustments:
        dr_name = aje.get("debit_account", "").strip()
        cr_name = aje.get("credit_account", "").strip()
        amt = float(aje.get("amount", 0.0))
        reason = aje.get("reason", "Year-End Audit Adjustment")

        if amt <= 0:
            continue

        total_adj_dr += amt
        total_adj_cr += amt

        # Find or create debit ledger
        dr_l = name_map.get(dr_name.lower())
        if dr_l:
            dr_l.debit += amt
        else:
            # Create new ledger if not in TB
            new_id = f"aje_dr_{len(ledger_map)}"
            dr_l = RawLedgerItem(
                id=new_id,
                name=dr_name,
                debit=amt,
                credit=0.0,
                original_group="Audit Adjustment",
                assigned_group=ICAIGroup.UNMAPPED,
                notes=f"Created via AJE: {reason}"
            )
            ledgers.append(dr_l)
            ledger_map[new_id] = dr_l
            name_map[dr_name.lower()] = dr_l

        # Find or create credit ledger
        cr_l = name_map.get(cr_name.lower())
        if cr_l:
            cr_l.credit += amt
        else:
            new_id = f"aje_cr_{len(ledger_map)}"
            cr_l = RawLedgerItem(
                id=new_id,
                name=cr_name,
                debit=0.0,
                credit=amt,
                original_group="Audit Adjustment",
                assigned_group=ICAIGroup.UNMAPPED,
                notes=f"Created via AJE: {reason}"
            )
            ledgers.append(cr_l)
            ledger_map[new_id] = cr_l
            name_map[cr_name.lower()] = cr_l

        applied_list.append({
            "id": aje.get("id", f"aje_{len(applied_list)+1}"),
            "type": aje.get("type", "AJE"),
            "debit_account": dr_name,
            "credit_account": cr_name,
            "amount": amt,
            "reason": reason
        })

    return ledgers, {
        "total_adjustments_count": len(applied_list),
        "total_adj_debit": round(total_adj_dr, 2),
        "total_adj_credit": round(total_adj_cr, 2),
        "is_aje_balanced": abs(total_adj_dr - total_adj_cr) < 0.01,
        "adjustments": applied_list
    }
