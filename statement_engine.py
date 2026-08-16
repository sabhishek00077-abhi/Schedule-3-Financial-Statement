"""Statement Engine: Generates ICAI Non-Corporate Schedule III Balance Sheet, P&L, CFS, Notes, Ratios, PPE, Aging, and Audit Reports."""
from typing import List, Dict, Any, Tuple
from .models import RawLedgerItem, ICAIGroup, ICAI_GROUP_LABELS, EntityInfo
from .ratios_engine import compute_financial_ratios
from .audit_engine import determine_icai_entity_level, apply_audit_adjustments
from .ppe_engine import generate_ppe_schedule
from .aging_engine import generate_trade_receivables_aging, generate_trade_payables_aging
from .report_engine import generate_accounting_policies, generate_draft_audit_report

def calculate_group_balances(ledgers: List[RawLedgerItem]) -> Dict[str, Dict[str, Any]]:
    """Sums debits, credits, and net balances for each ICAI Schedule III group."""
    group_data: Dict[str, Dict[str, Any]] = {
        g.value: {
            "group": g.value,
            "label": ICAI_GROUP_LABELS.get(g, g.value),
            "total_debit": 0.0,
            "total_credit": 0.0,
            "net_debit": 0.0,
            "net_credit": 0.0,
            "items": []
        }
        for g in ICAIGroup
    }

    for item in ledgers:
        grp = item.assigned_group.value if isinstance(item.assigned_group, ICAIGroup) else str(item.assigned_group)
        if grp not in group_data:
            grp = ICAIGroup.UNMAPPED.value
            
        group_data[grp]["total_debit"] += item.debit
        group_data[grp]["total_credit"] += item.credit
        group_data[grp]["items"].append({
            "id": item.id,
            "name": item.name,
            "code": item.code,
            "debit": item.debit,
            "credit": item.credit,
            "net": round(item.debit - item.credit, 2)
        })

    for grp, data in group_data.items():
        data["total_debit"] = round(data["total_debit"], 2)
        data["total_credit"] = round(data["total_credit"], 2)
        data["net_debit"] = round(data["total_debit"] - data["total_credit"], 2)
        data["net_credit"] = round(data["total_credit"] - data["total_debit"], 2)

    return group_data

def generate_financial_statements(
    ledgers: List[RawLedgerItem],
    entity: EntityInfo,
    adjustments: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generates complete ICAI Non-Corporate Balance Sheet, P&L, CFS, Notes, Ratios, PPE Schedule, Aging, and Audit Reports."""
    
    # Apply Adjusting Journal Entries (AJE) if any
    aje_meta = {"total_adjustments_count": 0, "adjustments": []}
    if adjustments:
        ledgers, aje_meta = apply_audit_adjustments(ledgers, adjustments)

    groups = calculate_group_balances(ledgers)
    
    # -------------------------------------------------------------
    # 1. STATEMENT OF PROFIT AND LOSS
    # -------------------------------------------------------------
    rev_operations = groups[ICAIGroup.REVENUE_OPERATIONS.value]["net_credit"]
    other_income = groups[ICAIGroup.OTHER_INCOME.value]["net_credit"]
    total_income = round(rev_operations + other_income, 2)

    cost_materials = groups[ICAIGroup.COST_OF_MATERIALS.value]["net_debit"]
    purchases_stock = groups[ICAIGroup.PURCHASES_STOCK_IN_TRADE.value]["net_debit"]
    changes_inv = groups[ICAIGroup.CHANGES_INVENTORIES.value]["net_debit"]
    employee_exp = groups[ICAIGroup.EMPLOYEE_BENEFITS.value]["net_debit"]
    finance_costs = groups[ICAIGroup.FINANCE_COSTS.value]["net_debit"]
    depr_expense = groups[ICAIGroup.DEPRECIATION_AMORTISATION.value]["net_debit"]
    other_exp = groups[ICAIGroup.OTHER_EXPENSES.value]["net_debit"]

    total_expenses = round(
        cost_materials + purchases_stock + changes_inv +
        employee_exp + finance_costs + depr_expense + other_exp,
        2
    )

    profit_before_tax = round(total_income - total_expenses, 2)
    tax_expense = groups[ICAIGroup.TAX_EXPENSE.value]["net_debit"]
    profit_after_tax = round(profit_before_tax - tax_expense, 2)

    # -------------------------------------------------------------
    # 2. BALANCE SHEET (ICAI Non-Corporate Entity Format)
    # -------------------------------------------------------------
    tb_cy_profit_items = [
        it for it in groups[ICAIGroup.RESERVES_SURPLUS.value]["items"]
        if "current year" in it["name"].lower() or "cy profit" in it["name"].lower()
    ]
    tb_cy_profit_val = sum(it["credit"] - it["debit"] for it in tb_cy_profit_items)
    
    base_reserves = round(
        groups[ICAIGroup.RESERVES_SURPLUS.value]["net_credit"] - tb_cy_profit_val,
        2
    )
    total_reserves_surplus = round(base_reserves + profit_after_tax, 2)
    
    owners_capital = groups[ICAIGroup.OWNERS_CAPITAL.value]["net_credit"]
    total_owners_funds = round(owners_capital + total_reserves_surplus, 2)

    # Non-Current Liabilities
    lt_borrowings = groups[ICAIGroup.LONG_TERM_BORROWINGS.value]["net_credit"]
    def_tax_liab = groups[ICAIGroup.DEFERRED_TAX_LIABILITY.value]["net_credit"]
    other_lt_liab = groups[ICAIGroup.OTHER_LONG_TERM_LIABILITIES.value]["net_credit"]
    lt_provisions = groups[ICAIGroup.LONG_TERM_PROVISIONS.value]["net_credit"]
    total_non_current_liab = round(lt_borrowings + def_tax_liab + other_lt_liab + lt_provisions, 2)

    # Current Liabilities
    st_borrowings = groups[ICAIGroup.SHORT_TERM_BORROWINGS.value]["net_credit"]
    trade_payables = groups[ICAIGroup.TRADE_PAYABLES.value]["net_credit"]
    other_cur_liab = groups[ICAIGroup.OTHER_CURRENT_LIABILITIES.value]["net_credit"]
    st_provisions = groups[ICAIGroup.SHORT_TERM_PROVISIONS.value]["net_credit"]
    total_current_liab = round(st_borrowings + trade_payables + other_cur_liab + st_provisions, 2)

    total_equity_liabilities = round(total_owners_funds + total_non_current_liab + total_current_liab, 2)

    # Assets
    ppe_gross = groups[ICAIGroup.PPE_GROSS.value]["net_debit"]
    ppe_acc_dep = groups[ICAIGroup.PPE_ACC_DEP.value]["net_credit"]
    ppe_net = round(ppe_gross - ppe_acc_dep, 2)
    intangible_assets = groups[ICAIGroup.INTANGIBLE_ASSETS.value]["net_debit"]
    non_cur_investments = groups[ICAIGroup.NON_CURRENT_INVESTMENTS.value]["net_debit"]
    def_tax_assets = groups[ICAIGroup.DEFERRED_TAX_ASSET.value]["net_debit"]
    lt_loans_adv = groups[ICAIGroup.LONG_TERM_LOANS_ADVANCES.value]["net_debit"]
    other_non_cur_assets = groups[ICAIGroup.OTHER_NON_CURRENT_ASSETS.value]["net_debit"]
    total_non_current_assets = round(
        ppe_net + intangible_assets + non_cur_investments + def_tax_assets + lt_loans_adv + other_non_cur_assets,
        2
    )

    cur_investments = groups[ICAIGroup.CURRENT_INVESTMENTS.value]["net_debit"]
    inventories = groups[ICAIGroup.INVENTORIES.value]["net_debit"]
    trade_receivables = groups[ICAIGroup.TRADE_RECEIVABLES.value]["net_debit"]
    cash_bank_balances = groups[ICAIGroup.CASH_BANK_BALANCES.value]["net_debit"]
    st_loans_adv = groups[ICAIGroup.SHORT_TERM_LOANS_ADVANCES.value]["net_debit"]
    other_cur_assets = groups[ICAIGroup.OTHER_CURRENT_ASSETS.value]["net_debit"]
    total_current_assets = round(
        cur_investments + inventories + trade_receivables + cash_bank_balances + st_loans_adv + other_cur_assets,
        2
    )

    total_assets = round(total_non_current_assets + total_current_assets, 2)
    bs_difference = round(total_equity_liabilities - total_assets, 2)

    # -------------------------------------------------------------
    # 3. CASH FLOW STATEMENT (AS-3 Indirect Method)
    # -------------------------------------------------------------
    cfo_net_profit = profit_before_tax
    cfo_depr_add = depr_expense
    cfo_finance_add = finance_costs
    cfo_other_inc_less = -other_income
    operating_profit_before_wc = round(
        cfo_net_profit + cfo_depr_add + cfo_finance_add + cfo_other_inc_less,
        2
    )

    wc_inventories = -inventories
    wc_receivables = -trade_receivables
    wc_st_advances = -st_loans_adv
    wc_other_ca = -other_cur_assets
    wc_payables = trade_payables
    wc_other_cl = other_cur_liab
    wc_provisions = st_provisions

    total_wc_change = round(
        wc_inventories + wc_receivables + wc_st_advances + wc_other_ca +
        wc_payables + wc_other_cl + wc_provisions,
        2
    )
    cash_generated_from_ops = round(operating_profit_before_wc + total_wc_change, 2)
    taxes_paid = -tax_expense
    net_cfo = round(cash_generated_from_ops + taxes_paid, 2)

    cfi_capex = -ppe_gross
    cfi_investments = -(non_cur_investments + cur_investments)
    cfi_interest_received = other_income
    net_cfi = round(cfi_capex + cfi_investments + cfi_interest_received, 2)

    cff_capital = owners_capital
    cff_reserves = base_reserves
    cff_lt_borrowing = lt_borrowings
    cff_st_borrowing = st_borrowings
    cff_interest_paid = -finance_costs
    net_cff = round(
        cff_capital + cff_reserves + cff_lt_borrowing + cff_st_borrowing + cff_interest_paid,
        2
    )

    net_cash_flow = round(net_cfo + net_cfi + net_cff, 2)
    opening_cash = round(cash_bank_balances - net_cash_flow, 2)
    closing_cash = round(opening_cash + net_cash_flow, 2)
    cfs_reconciled = (round(closing_cash, 2) == round(cash_bank_balances, 2))

    # -------------------------------------------------------------
    # 4. NOTES TO ACCOUNTS
    # -------------------------------------------------------------
    notes: List[Dict[str, Any]] = []
    note_counter = 1

    note_defs = [
        (ICAIGroup.OWNERS_CAPITAL, "Owner's / Partners' Capital Accounts", owners_capital),
        (ICAIGroup.RESERVES_SURPLUS, "Reserves and Surplus", total_reserves_surplus),
        (ICAIGroup.LONG_TERM_BORROWINGS, "Long-Term Borrowings", lt_borrowings),
        (ICAIGroup.OTHER_LONG_TERM_LIABILITIES, "Other Long-Term Liabilities", other_lt_liab),
        (ICAIGroup.LONG_TERM_PROVISIONS, "Long-Term Provisions", lt_provisions),
        (ICAIGroup.SHORT_TERM_BORROWINGS, "Short-Term Borrowings", st_borrowings),
        (ICAIGroup.TRADE_PAYABLES, "Trade Payables", trade_payables),
        (ICAIGroup.OTHER_CURRENT_LIABILITIES, "Other Current Liabilities", other_cur_liab),
        (ICAIGroup.SHORT_TERM_PROVISIONS, "Short-Term Provisions", st_provisions),
        
        (ICAIGroup.PPE_GROSS, "Property, Plant and Equipment (PPE)", ppe_net),
        (ICAIGroup.INTANGIBLE_ASSETS, "Intangible Assets", intangible_assets),
        (ICAIGroup.NON_CURRENT_INVESTMENTS, "Non-Current Investments", non_cur_investments),
        (ICAIGroup.LONG_TERM_LOANS_ADVANCES, "Long-Term Loans and Advances", lt_loans_adv),
        (ICAIGroup.OTHER_NON_CURRENT_ASSETS, "Other Non-Current Assets", other_non_cur_assets),
        (ICAIGroup.CURRENT_INVESTMENTS, "Current Investments", cur_investments),
        (ICAIGroup.INVENTORIES, "Inventories", inventories),
        (ICAIGroup.TRADE_RECEIVABLES, "Trade Receivables", trade_receivables),
        (ICAIGroup.CASH_BANK_BALANCES, "Cash and Bank Balances", cash_bank_balances),
        (ICAIGroup.SHORT_TERM_LOANS_ADVANCES, "Short-Term Loans and Advances", st_loans_adv),
        (ICAIGroup.OTHER_CURRENT_ASSETS, "Other Current Assets", other_cur_assets),
        
        (ICAIGroup.REVENUE_OPERATIONS, "Revenue from Operations", rev_operations),
        (ICAIGroup.OTHER_INCOME, "Other Income", other_income),
        (ICAIGroup.COST_OF_MATERIALS, "Cost of Materials Consumed", cost_materials),
        (ICAIGroup.PURCHASES_STOCK_IN_TRADE, "Purchases of Stock-in-Trade / COGS", purchases_stock),
        (ICAIGroup.EMPLOYEE_BENEFITS, "Employee Benefits Expense", employee_exp),
        (ICAIGroup.FINANCE_COSTS, "Finance Costs", finance_costs),
        (ICAIGroup.DEPRECIATION_AMORTISATION, "Depreciation and Amortisation Expense", depr_expense),
        (ICAIGroup.OTHER_EXPENSES, "Other Expenses", other_exp)
    ]

    note_map: Dict[str, int] = {}
    for grp_enum, title, grp_total in note_defs:
        grp_val = grp_enum.value
        g_data = groups[grp_val]
        
        if g_data["items"] or (grp_enum == ICAIGroup.PPE_GROSS and groups[ICAIGroup.PPE_ACC_DEP.value]["items"]):
            items_list = list(g_data["items"])
            if grp_enum == ICAIGroup.PPE_GROSS and groups[ICAIGroup.PPE_ACC_DEP.value]["items"]:
                for dep_it in groups[ICAIGroup.PPE_ACC_DEP.value]["items"]:
                    items_list.append({
                        "id": dep_it["id"],
                        "name": f"Less: {dep_it['name']}",
                        "code": dep_it["code"],
                        "debit": 0.0,
                        "credit": dep_it["credit"],
                        "net": -dep_it["credit"]
                    })
            if grp_enum == ICAIGroup.RESERVES_SURPLUS:
                items_list.append({
                    "id": "pnl_cy_profit",
                    "name": "Add: Profit for the year (as per P&L)",
                    "code": "",
                    "debit": 0.0,
                    "credit": profit_after_tax,
                    "net": profit_after_tax
                })

            note_map[grp_val] = note_counter
            notes.append({
                "note_number": note_counter,
                "title": title,
                "group_key": grp_val,
                "total": grp_total,
                "items": items_list
            })
            note_counter += 1

    # Base statement structure
    bs_dict = {
        "equity_and_liabilities": {
            "owners_funds": {
                "owners_capital": {"amount": owners_capital, "note": note_map.get(ICAIGroup.OWNERS_CAPITAL.value)},
                "reserves_and_surplus": {"amount": total_reserves_surplus, "note": note_map.get(ICAIGroup.RESERVES_SURPLUS.value)},
                "total": total_owners_funds
            },
            "non_current_liabilities": {
                "long_term_borrowings": {"amount": lt_borrowings, "note": note_map.get(ICAIGroup.LONG_TERM_BORROWINGS.value)},
                "deferred_tax_liabilities": {"amount": def_tax_liab, "note": note_map.get(ICAIGroup.DEFERRED_TAX_LIABILITY.value)},
                "other_long_term_liabilities": {"amount": other_lt_liab, "note": note_map.get(ICAIGroup.OTHER_LONG_TERM_LIABILITIES.value)},
                "long_term_provisions": {"amount": lt_provisions, "note": note_map.get(ICAIGroup.LONG_TERM_PROVISIONS.value)},
                "total": total_non_current_liab
            },
            "current_liabilities": {
                "short_term_borrowings": {"amount": st_borrowings, "note": note_map.get(ICAIGroup.SHORT_TERM_BORROWINGS.value)},
                "trade_payables": {"amount": trade_payables, "note": note_map.get(ICAIGroup.TRADE_PAYABLES.value)},
                "other_current_liabilities": {"amount": other_cur_liab, "note": note_map.get(ICAIGroup.OTHER_CURRENT_LIABILITIES.value)},
                "short_term_provisions": {"amount": st_provisions, "note": note_map.get(ICAIGroup.SHORT_TERM_PROVISIONS.value)},
                "total": total_current_liab
            },
            "total": total_equity_liabilities
        },
        "assets": {
            "non_current_assets": {
                "ppe_net": {"gross": ppe_gross, "acc_dep": ppe_acc_dep, "amount": ppe_net, "note": note_map.get(ICAIGroup.PPE_GROSS.value)},
                "intangible_assets": {"amount": intangible_assets, "note": note_map.get(ICAIGroup.INTANGIBLE_ASSETS.value)},
                "non_current_investments": {"amount": non_cur_investments, "note": note_map.get(ICAIGroup.NON_CURRENT_INVESTMENTS.value)},
                "deferred_tax_assets": {"amount": def_tax_assets, "note": note_map.get(ICAIGroup.DEFERRED_TAX_ASSET.value)},
                "long_term_loans_advances": {"amount": lt_loans_adv, "note": note_map.get(ICAIGroup.LONG_TERM_LOANS_ADVANCES.value)},
                "other_non_current_assets": {"amount": other_non_cur_assets, "note": note_map.get(ICAIGroup.OTHER_NON_CURRENT_ASSETS.value)},
                "total": total_non_current_assets
            },
            "current_assets": {
                "current_investments": {"amount": cur_investments, "note": note_map.get(ICAIGroup.CURRENT_INVESTMENTS.value)},
                "inventories": {"amount": inventories, "note": note_map.get(ICAIGroup.INVENTORIES.value)},
                "trade_receivables": {"amount": trade_receivables, "note": note_map.get(ICAIGroup.TRADE_RECEIVABLES.value)},
                "cash_and_bank_balances": {"amount": cash_bank_balances, "note": note_map.get(ICAIGroup.CASH_BANK_BALANCES.value)},
                "short_term_loans_advances": {"amount": st_loans_adv, "note": note_map.get(ICAIGroup.SHORT_TERM_LOANS_ADVANCES.value)},
                "other_current_assets": {"amount": other_cur_assets, "note": note_map.get(ICAIGroup.OTHER_CURRENT_ASSETS.value)},
                "total": total_current_assets
            },
            "total": total_assets
        },
        "is_balanced": abs(bs_difference) < 0.01,
        "difference": bs_difference
    }

    pnl_dict = {
        "income": {
            "revenue_from_operations": {"amount": rev_operations, "note": note_map.get(ICAIGroup.REVENUE_OPERATIONS.value)},
            "other_income": {"amount": other_income, "note": note_map.get(ICAIGroup.OTHER_INCOME.value)},
            "total": total_income
        },
        "expenses": {
            "cost_of_materials": {"amount": cost_materials, "note": note_map.get(ICAIGroup.COST_OF_MATERIALS.value)},
            "purchases_stock_in_trade": {"amount": purchases_stock, "note": note_map.get(ICAIGroup.PURCHASES_STOCK_IN_TRADE.value)},
            "changes_in_inventories": {"amount": changes_inv, "note": note_map.get(ICAIGroup.CHANGES_INVENTORIES.value)},
            "employee_benefits": {"amount": employee_exp, "note": note_map.get(ICAIGroup.EMPLOYEE_BENEFITS.value)},
            "finance_costs": {"amount": finance_costs, "note": note_map.get(ICAIGroup.FINANCE_COSTS.value)},
            "depreciation_amortisation": {"amount": depr_expense, "note": note_map.get(ICAIGroup.DEPRECIATION_AMORTISATION.value)},
            "other_expenses": {"amount": other_exp, "note": note_map.get(ICAIGroup.OTHER_EXPENSES.value)},
            "total": total_expenses
        },
        "profit_before_tax": profit_before_tax,
        "tax_expense": {"amount": tax_expense, "note": note_map.get(ICAIGroup.TAX_EXPENSE.value)},
        "profit_after_tax": profit_after_tax
    }

    # -------------------------------------------------------------
    # 5. BIG 4 ENGINES: RATIOS, LEVEL, PPE, AGING, AUDIT REPORT
    # -------------------------------------------------------------
    ratios_list = compute_financial_ratios(bs_dict, pnl_dict)
    entity_level_info = determine_icai_entity_level(turnover=total_income, borrowings=total_non_current_liab + total_current_liab)
    ppe_schedule = generate_ppe_schedule(ledgers, cy_depr_expense=depr_expense)
    rec_aging = generate_trade_receivables_aging(trade_receivables)
    pay_aging = generate_trade_payables_aging(trade_payables)
    policies = generate_accounting_policies(entity)
    audit_report = generate_draft_audit_report(entity, abs(bs_difference) < 0.01, profit_after_tax)

    return {
        "entity": {
            "name": entity.name,
            "entity_type": entity.entity_type,
            "financial_year": entity.financial_year,
            "as_on_date": entity.as_on_date,
            "currency_symbol": entity.currency_symbol,
            "round_off": entity.round_off
        },
        "entity_level": entity_level_info,
        "balance_sheet": bs_dict,
        "profit_and_loss": pnl_dict,
        "cash_flow_statement": {
            "operating_activities": {
                "net_profit_before_tax": cfo_net_profit,
                "adjustments": [
                    {"label": "Depreciation & Amortisation Expense", "amount": cfo_depr_add},
                    {"label": "Finance Costs (Interest Expense)", "amount": cfo_finance_add},
                    {"label": "Less: Non-Operating Income (Interest / Dividend)", "amount": cfo_other_inc_less}
                ],
                "operating_profit_before_wc": operating_profit_before_wc,
                "working_capital_changes": [
                    {"label": "(Increase) / Decrease in Inventories", "amount": wc_inventories},
                    {"label": "(Increase) / Decrease in Trade Receivables", "amount": wc_receivables},
                    {"label": "(Increase) / Decrease in Short-Term Loans & Advances", "amount": wc_st_advances},
                    {"label": "(Increase) / Decrease in Other Current Assets", "amount": wc_other_ca},
                    {"label": "Increase / (Decrease) in Trade Payables", "amount": wc_payables},
                    {"label": "Increase / (Decrease) in Other Current Liabilities", "amount": wc_other_cl},
                    {"label": "Increase / (Decrease) in Short-Term Provisions", "amount": wc_provisions}
                ],
                "cash_generated_from_operations": cash_generated_from_ops,
                "taxes_paid": taxes_paid,
                "net_cash_from_operating_activities": net_cfo
            },
            "investing_activities": {
                "items": [
                    {"label": "Purchase of Property, Plant & Equipment", "amount": cfi_capex},
                    {"label": "Purchase / Sale of Investments (Net)", "amount": cfi_investments},
                    {"label": "Interest / Dividend Income Received", "amount": cfi_interest_received}
                ],
                "net_cash_from_investing_activities": net_cfi
            },
            "financing_activities": {
                "items": [
                    {"label": "Owners' / Partners' Capital Introduced / (Drawings)", "amount": cff_capital},
                    {"label": "Movement in General Reserves / Capital Reserves", "amount": cff_reserves},
                    {"label": "Proceeds / (Repayment) of Long-Term Borrowings", "amount": cff_lt_borrowing},
                    {"label": "Proceeds / (Repayment) of Short-Term Borrowings", "amount": cff_st_borrowing},
                    {"label": "Finance Costs Paid", "amount": cff_interest_paid}
                ],
                "net_cash_from_financing_activities": net_cff
            },
            "summary": {
                "net_increase_decrease_cash": net_cash_flow,
                "opening_cash_and_cash_equivalents": opening_cash,
                "closing_cash_and_cash_equivalents": closing_cash,
                "balance_sheet_cash": cash_bank_balances,
                "is_reconciled": cfs_reconciled
            }
        },
        "notes": notes,
        "financial_ratios": ratios_list,
        "ppe_schedule": ppe_schedule,
        "aging_schedules": {
            "receivables": rec_aging,
            "payables": pay_aging
        },
        "accounting_policies": policies,
        "audit_report": audit_report,
        "audit_adjustments": aje_meta,
        "diagnostics": {
            "total_ledgers": len(ledgers),
            "unmapped_ledgers": [it for it in ledgers if it.assigned_group == ICAIGroup.UNMAPPED],
            "total_debit_tb": sum(l.debit for l in ledgers),
            "total_credit_tb": sum(l.credit for l in ledgers),
            "tb_balanced": abs(sum(l.debit for l in ledgers) - sum(l.credit for l in ledgers)) < 0.01
        }
    }
