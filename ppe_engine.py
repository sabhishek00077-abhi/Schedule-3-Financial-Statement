"""AS 10 Property, Plant and Equipment (PPE) Schedule Engine."""
from typing import Dict, Any, List
from .models import RawLedgerItem, ICAIGroup

PPE_CATEGORIES = [
    {"key": "land", "name": "Freehold Land", "rate": "0.0%"},
    {"key": "buildings", "name": "Factory & Office Buildings", "rate": "5.0% - 10.0%"},
    {"key": "plant_machinery", "name": "Plant and Machinery", "rate": "15.0%"},
    {"key": "equipment", "name": "Office & Operating Equipment", "rate": "15.0%"},
    {"key": "furniture", "name": "Furniture and Fixtures", "rate": "10.0%"},
    {"key": "vehicles", "name": "Motor Vehicles & Trucks", "rate": "15.0% - 20.0%"},
    {"key": "computers", "name": "Computers & IT Hardware", "rate": "40.0%"}
]

def generate_ppe_schedule(ledgers: List[RawLedgerItem], cy_depr_expense: float = 0.0) -> Dict[str, Any]:
    """Generates comprehensive AS 10 Fixed Asset (PPE) schedule with Gross Block, Depreciation, and Net Block."""
    ppe_items = [l for l in ledgers if l.assigned_group == ICAIGroup.PPE_GROSS]
    dep_items = [l for l in ledgers if l.assigned_group == ICAIGroup.PPE_ACC_DEP]

    rows = []
    tot_gross_open = 0.0
    tot_additions = 0.0
    tot_deletions = 0.0
    tot_gross_close = 0.0
    
    tot_dep_open = 0.0
    tot_dep_for_year = 0.0
    tot_dep_close = 0.0
    
    tot_net_open = 0.0
    tot_net_close = 0.0

    # Group PPE ledgers into recognizable asset classes
    for cat in PPE_CATEGORIES:
        k = cat["key"]
        matched_gross = [
            it for it in ppe_items
            if k in it.name.lower() or (k == "equipment" and ("equip" in it.name.lower() or "machin" not in it.name.lower() and "furn" not in it.name.lower() and "build" not in it.name.lower()))
        ]
        matched_dep = [
            it for it in dep_items
            if k in it.name.lower() or (k == "equipment" and "equip" in it.name.lower()) or (k == "buildings" and "build" in it.name.lower())
        ]

        gross_val = sum(it.debit for it in matched_gross)
        acc_dep_val = sum(it.credit for it in matched_dep)

        if gross_val > 0 or acc_dep_val > 0:
            # Estimate additions / opening split
            gross_open = gross_val
            additions = 0.0
            deletions = 0.0
            gross_close = gross_val

            dep_for_year = round(gross_val * (0.05 if "build" in k else 0.10), 2) if cy_depr_expense > 0 else 0.0
            dep_open = max(0.0, acc_dep_val - dep_for_year) if acc_dep_val > 0 else 0.0
            dep_close = acc_dep_val if acc_dep_val > 0 else dep_for_year

            net_open = round(gross_open - dep_open, 2)
            net_close = round(gross_close - dep_close, 2)

            rows.append({
                "category": cat["name"],
                "depreciation_rate": cat["rate"],
                "gross_block": {
                    "opening": gross_open,
                    "additions": additions,
                    "deletions": deletions,
                    "closing": gross_close
                },
                "depreciation": {
                    "opening": dep_open,
                    "for_the_year": dep_for_year,
                    "deletions": 0.0,
                    "closing": dep_close
                },
                "net_block": {
                    "opening": net_open,
                    "closing": net_close
                }
            })

            tot_gross_open += gross_open
            tot_additions += additions
            tot_deletions += deletions
            tot_gross_close += gross_close
            tot_dep_open += dep_open
            tot_dep_for_year += dep_for_year
            tot_dep_close += dep_close
            tot_net_open += net_open
            tot_net_close += net_close

    # Fallback if no specific categories matched
    if not rows and ppe_items:
        g_val = sum(l.debit for l in ppe_items)
        d_val = sum(l.credit for l in dep_items)
        rows.append({
            "category": "General Plant, Equipment & Fixed Assets",
            "depreciation_rate": "10.0%",
            "gross_block": {"opening": g_val, "additions": 0.0, "deletions": 0.0, "closing": g_val},
            "depreciation": {"opening": d_val, "for_the_year": cy_depr_expense, "deletions": 0.0, "closing": d_val},
            "net_block": {"opening": round(g_val - d_val, 2), "closing": round(g_val - d_val, 2)}
        })
        tot_gross_close = g_val
        tot_dep_close = d_val
        tot_net_close = round(g_val - d_val, 2)

    return {
        "rows": rows,
        "totals": {
            "gross_block": {
                "opening": round(tot_gross_open, 2),
                "additions": round(tot_additions, 2),
                "deletions": round(tot_deletions, 2),
                "closing": round(tot_gross_close, 2)
            },
            "depreciation": {
                "opening": round(tot_dep_open, 2),
                "for_the_year": round(tot_dep_for_year, 2),
                "deletions": 0.0,
                "closing": round(tot_dep_close, 2)
            },
            "net_block": {
                "opening": round(tot_net_open, 2),
                "closing": round(tot_net_close, 2)
            }
        }
    }
