"""ICAI Schedule III Mandatory 11 Key Financial Ratios & Analytical Review Engine."""
from typing import Dict, Any, List

def compute_financial_ratios(bs: Dict[str, Any], pnl: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Computes all 11 mandatory financial ratios prescribed under ICAI Schedule III guidelines."""
    eq_liab = bs.get("equity_and_liabilities", {})
    assets = bs.get("assets", {})
    income = pnl.get("income", {})
    expenses = pnl.get("expenses", {})

    # Key Totals
    revenue = income.get("revenue_from_operations", {}).get("amount", 0.0)
    total_income = income.get("total", 0.0)
    cogs = expenses.get("purchases_stock_in_trade", {}).get("amount", 0.0) or expenses.get("cost_of_materials", {}).get("amount", 0.0)
    net_profit = pnl.get("profit_after_tax", 0.0)
    pbt = pnl.get("profit_before_tax", 0.0)
    finance_costs = expenses.get("finance_costs", {}).get("amount", 0.0)
    depreciation = expenses.get("depreciation_amortisation", {}).get("amount", 0.0)
    ebit = round(pbt + finance_costs, 2)

    # Balance sheet components
    current_assets = assets.get("current_assets", {}).get("total", 0.0)
    current_liabilities = eq_liab.get("current_liabilities", {}).get("total", 0.0)
    working_capital = round(current_assets - current_liabilities, 2)

    owners_funds = eq_liab.get("owners_funds", {}).get("total", 0.0)
    lt_borrowings = eq_liab.get("non_current_liabilities", {}).get("long_term_borrowings", {}).get("amount", 0.0)
    st_borrowings = eq_liab.get("current_liabilities", {}).get("short_term_borrowings", {}).get("amount", 0.0)
    total_debt = round(lt_borrowings + st_borrowings, 2)
    capital_employed = round(owners_funds + lt_borrowings, 2)

    inventory = assets.get("current_assets", {}).get("inventories", {}).get("amount", 0.0)
    trade_receivables = assets.get("current_assets", {}).get("trade_receivables", {}).get("amount", 0.0)
    trade_payables = eq_liab.get("current_liabilities", {}).get("trade_payables", {}).get("amount", 0.0)
    
    non_cur_investments = assets.get("non_current_assets", {}).get("non_current_investments", {}).get("amount", 0.0)
    cur_investments = assets.get("current_assets", {}).get("current_investments", {}).get("amount", 0.0)
    total_investments = round(non_cur_investments + cur_investments, 2)
    other_income = income.get("other_income", {}).get("amount", 0.0)

    ratios = []

    # 1. Current Ratio
    cr_val = round(current_assets / current_liabilities, 2) if current_liabilities > 0 else 0.0
    ratios.append({
        "id": "current_ratio",
        "name": "Current Ratio",
        "formula": "Current Assets / Current Liabilities",
        "numerator": current_assets,
        "denominator": current_liabilities,
        "value": cr_val,
        "unit": "times",
        "benchmark": "1.33 - 2.00",
        "status": "Healthy" if cr_val >= 1.33 else ("Watchlist" if cr_val >= 1.0 else "Alert"),
        "interpretation": "Measures entity's short-term liquidity to satisfy current obligations."
    })

    # 2. Debt-Equity Ratio
    de_val = round(total_debt / owners_funds, 2) if owners_funds > 0 else 0.0
    ratios.append({
        "id": "debt_equity_ratio",
        "name": "Debt-Equity Ratio",
        "formula": "Total Debt / Owners' (Shareholders') Equity",
        "numerator": total_debt,
        "denominator": owners_funds,
        "value": de_val,
        "unit": "times",
        "benchmark": "< 2.00",
        "status": "Healthy" if de_val <= 1.5 else ("Watchlist" if de_val <= 2.5 else "Alert"),
        "interpretation": "Evaluates capital structure solvency and reliance on borrowed funds."
    })

    # 3. Debt Service Coverage Ratio (DSCR)
    dscr_den = finance_costs + (lt_borrowings * 0.15) # Assuming approx annual principal component
    dscr_num = ebit + depreciation
    dscr_val = round(dscr_num / dscr_den, 2) if dscr_den > 0 else (round(ebit / finance_costs, 2) if finance_costs > 0 else 0.0)
    ratios.append({
        "id": "dscr",
        "name": "Debt Service Coverage Ratio (DSCR)",
        "formula": "(EBITDA) / (Interest + Principal Repayments)",
        "numerator": dscr_num,
        "denominator": dscr_den,
        "value": dscr_val,
        "unit": "times",
        "benchmark": ">= 1.50",
        "status": "Healthy" if dscr_val >= 1.5 else ("Watchlist" if dscr_val >= 1.0 else "Alert"),
        "interpretation": "Assesses capacity to service interest and scheduled principal repayments."
    })

    # 4. Return on Equity / Partner Capital (ROE)
    roe_val = round((net_profit / owners_funds) * 100, 2) if owners_funds > 0 else 0.0
    ratios.append({
        "id": "return_on_equity",
        "name": "Return on Equity / Partner Capital (ROE)",
        "formula": "(Net Profit After Tax / Owners' Funds) * 100",
        "numerator": net_profit,
        "denominator": owners_funds,
        "value": roe_val,
        "unit": "%",
        "benchmark": "15.0% - 25.0%",
        "status": "Healthy" if roe_val >= 12.0 else ("Watchlist" if roe_val > 0 else "Alert"),
        "interpretation": "Profitability generated on capital contributed and retained by partners/owners."
    })

    # 5. Inventory Turnover Ratio
    inv_val = round(cogs / inventory, 2) if inventory > 0 else 0.0
    inv_days = round(365 / inv_val, 1) if inv_val > 0 else 0.0
    ratios.append({
        "id": "inventory_turnover",
        "name": "Inventory Turnover Ratio",
        "formula": "COGS / Average Inventory",
        "numerator": cogs,
        "denominator": inventory,
        "value": inv_val,
        "unit": "times",
        "extra_info": f"Holding Period: ~{inv_days} days",
        "benchmark": "4.00 - 8.00",
        "status": "Healthy" if inv_val >= 4.0 else ("Watchlist" if inv_val >= 2.0 else "Alert"),
        "interpretation": "Efficiency of inventory velocity and stock liquidation."
    })

    # 6. Trade Receivables Turnover Ratio
    rec_val = round(revenue / trade_receivables, 2) if trade_receivables > 0 else 0.0
    dso = round(365 / rec_val, 1) if rec_val > 0 else 0.0
    ratios.append({
        "id": "trade_receivables_turnover",
        "name": "Trade Receivables Turnover Ratio",
        "formula": "Revenue from Operations / Average Receivables",
        "numerator": revenue,
        "denominator": trade_receivables,
        "value": rec_val,
        "unit": "times",
        "extra_info": f"DSO (Collection Period): ~{dso} days",
        "benchmark": "6.00 - 12.00",
        "status": "Healthy" if rec_val >= 5.0 else ("Watchlist" if rec_val >= 3.0 else "Alert"),
        "interpretation": "Speed and effectiveness of debtor credit collection."
    })

    # 7. Trade Payables Turnover Ratio
    purchases_total = cogs
    pay_val = round(purchases_total / trade_payables, 2) if trade_payables > 0 else 0.0
    dpo = round(365 / pay_val, 1) if pay_val > 0 else 0.0
    ratios.append({
        "id": "trade_payables_turnover",
        "name": "Trade Payables Turnover Ratio",
        "formula": "Net Purchases / Average Trade Payables",
        "numerator": purchases_total,
        "denominator": trade_payables,
        "value": pay_val,
        "unit": "times",
        "extra_info": f"DPO (Payment Period): ~{dpo} days",
        "benchmark": "4.00 - 8.00",
        "status": "Healthy" if pay_val >= 3.0 else "Watchlist",
        "interpretation": "Velocity of settling vendor payables and trade liabilities."
    })

    # 8. Net Capital Turnover Ratio
    nct_val = round(revenue / working_capital, 2) if working_capital > 0 else 0.0
    ratios.append({
        "id": "net_capital_turnover",
        "name": "Net Capital Turnover Ratio",
        "formula": "Revenue from Operations / Working Capital",
        "numerator": revenue,
        "denominator": working_capital,
        "value": nct_val,
        "unit": "times",
        "benchmark": "3.00 - 6.00",
        "status": "Healthy" if nct_val > 0 else "Alert",
        "interpretation": "Revenue productivity generated per unit of net working capital."
    })

    # 9. Net Profit Margin (%)
    npm_val = round((net_profit / revenue) * 100, 2) if revenue > 0 else 0.0
    ratios.append({
        "id": "net_profit_margin",
        "name": "Net Profit Margin (%)",
        "formula": "(Net Profit for the Year / Revenue from Operations) * 100",
        "numerator": net_profit,
        "denominator": revenue,
        "value": npm_val,
        "unit": "%",
        "benchmark": "10.0% - 25.0%",
        "status": "Healthy" if npm_val >= 10.0 else ("Watchlist" if npm_val > 0 else "Alert"),
        "interpretation": "Net profitability retained per rupee of top-line revenue."
    })

    # 10. Return on Capital Employed (ROCE)
    roce_val = round((ebit / capital_employed) * 100, 2) if capital_employed > 0 else 0.0
    ratios.append({
        "id": "return_on_capital_employed",
        "name": "Return on Capital Employed (ROCE)",
        "formula": "(EBIT / Capital Employed) * 100",
        "numerator": ebit,
        "denominator": capital_employed,
        "value": roce_val,
        "unit": "%",
        "benchmark": "15.0% - 30.0%",
        "status": "Healthy" if roce_val >= 14.0 else ("Watchlist" if roce_val > 0 else "Alert"),
        "interpretation": "Operating yield generated on long-term funds committed to operations."
    })

    # 11. Return on Investment (ROI)
    roi_val = round((other_income / total_investments) * 100, 2) if total_investments > 0 else 0.0
    ratios.append({
        "id": "return_on_investment",
        "name": "Return on Investment (ROI)",
        "formula": "(Income from Investments / Cost of Investments) * 100",
        "numerator": other_income,
        "denominator": total_investments,
        "value": roi_val,
        "unit": "%",
        "benchmark": "7.0% - 12.0%",
        "status": "Healthy" if roi_val >= 6.0 else "Watchlist",
        "interpretation": "Annualized yield generated from surplus treasury and financial assets."
    })

    return ratios
