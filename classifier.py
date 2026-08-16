"""Intelligent rule and keyword classifier for ICAI Schedule III Non-Corporate heads."""
import re
from typing import Tuple
from .models import ICAIGroup

# Keyword mapping rules with priority weights
RULES = [
    # 1. Accumulated Depreciation / Contra-Assets
    (
        r"(accumulated\s*depr|prov(ision)?\s*for\s*depr|depreciation\s*reserve)",
        ICAIGroup.PPE_ACC_DEP,
        0.98
    ),
    
    # 2. Fixed Assets / Property Plant & Equipment (Gross)
    (
        r"(building|land|factory|plant\s*(&|and)?\s*machinery|machinery|equipment|furniture(\s*(&|and)?\s*fixtures)?|vehicle|motor\s*car|truck|computer|laptop|office\s*equipment|electrical\s*installation)",
        ICAIGroup.PPE_GROSS,
        0.95
    ),
    
    # 3. Intangible Assets
    (
        r"(goodwill|patent|trademark|brand|software|license|copyright|technical\s*knowhow)",
        ICAIGroup.INTANGIBLE_ASSETS,
        0.95
    ),
    
    # 4. Cash and Bank Balances
    (
        r"(cash\s*at\s*bank|bank\s*a/?c|current\s*a/?c|savings\s*a/?c|hdfc|icici|sbi|axis|pnb|kotak|bank\s*of\s*baroda|petty\s*cash|cash\s*in\s*hand|cash\s*balance|cheque(s)?\s*in\s*hand)",
        ICAIGroup.CASH_BANK_BALANCES,
        0.95
    ),

    # 5. Inventories
    (
        r"(inventory|closing\s*stock|stock\s*in\s*trade|raw\s*material(s)?|work\s*in\s*progress|wip|finished\s*goods|packing\s*material)",
        ICAIGroup.INVENTORIES,
        0.95
    ),

    # 6. Trade Receivables / Debtors
    (
        r"(account(s)?\s*receivable|sundry\s*debtor(s)?|trade\s*debtor(s)?|trade\s*receivable(s)?|bills\s*receivable|customer(s)?\s*balance)",
        ICAIGroup.TRADE_RECEIVABLES,
        0.95
    ),

    # 7. Short-Term Loans & Advances / Prepaid / GST
    (
        r"(prepaid\s*expense(s)?|advance\s*to\s*supplier(s)?|staff\s*advance(s)?|advance\s*tax|tds\s*receivable|gst\s*itc|gst\s*input|gst\s*cash\s*ledger|gst\s*credit\s*ledger|input\s*tax\s*credit)",
        ICAIGroup.SHORT_TERM_LOANS_ADVANCES,
        0.92
    ),

    # 8. Long-Term Loans & Advances / Security Deposits
    (
        r"(security\s*deposit|electricity\s*deposit|rent\s*deposit|telephone\s*deposit|capital\s*advance)",
        ICAIGroup.LONG_TERM_LOANS_ADVANCES,
        0.90
    ),

    # 9. Non-Current Investments
    (
        r"(investment\s*in\s*property|non-current\s*investment|long\s*term\s*investment|shares\s*in|investment\s*in\s*equity|government\s*securities|nsc|kisan\s*vikas)",
        ICAIGroup.NON_CURRENT_INVESTMENTS,
        0.90
    ),

    # 10. Current Investments
    (
        r"(current\s*investment|mutual\s*fund|liquid\s*fund|marketable\s*securit|treasury\s*bill|commercial\s*paper)",
        ICAIGroup.CURRENT_INVESTMENTS,
        0.90
    ),

    # 11. Short-Term Borrowings (Check before Long-term)
    (
        r"(short[\s-]*term\s*loan|short[\s-]*term\s*borrowing|bank\s*overdraft|overdraft|cash\s*credit|cc\s*limit|working\s*capital\s*loan|loan\s*repayable\s*on\s*demand)",
        ICAIGroup.SHORT_TERM_BORROWINGS,
        0.96
    ),

    # 12. Long-Term Borrowings
    (
        r"(long[\s-]*term\s*loan|long[\s-]*term\s*borrowing|term\s*loan|secured\s*loan|unsecured\s*loan|mortgage\s*loan|bank\s*loan\s*\(?lt\)?|borrowing(s)?\s*from\s*director)",
        ICAIGroup.LONG_TERM_BORROWINGS,
        0.95
    ),

    # 13. Owners' Capital
    (
        r"(capital\s*stock|share\s*capital|owner('s)?\s*capital|partner('s)?\s*capital|proprietor('s)?\s*capital|drawing(s)?|partner\s*current\s*a/?c)",
        ICAIGroup.OWNERS_CAPITAL,
        0.95
    ),

    # 14. Reserves and Surplus
    (
        r"(retained\s*earnings|general\s*reserve|capital\s*reserve|securities\s*premium|surplus|current\s*year\s*profit|p\s*(&|and)\s*l\s*balance)",
        ICAIGroup.RESERVES_SURPLUS,
        0.92
    ),

    # 15. Trade Payables / Creditors
    (
        r"(account(s)?\s*payable|sundry\s*creditor(s)?|trade\s*creditor(s)?|trade\s*payable(s)?|bills\s*payable|vendor(s)?\s*payable)",
        ICAIGroup.TRADE_PAYABLES,
        0.95
    ),

    # 16. Other Current Liabilities
    (
        r"(salar(y|ies)\s*payable|wages\s*payable|rent\s*payable|outstanding\s*expense(s)?|interest\s*payable|gst\s*payable|tds\s*payable|pf\s*payable|esic\s*payable|duties\s*(&|and)?\s*taxes|advance\s*from\s*customer)",
        ICAIGroup.OTHER_CURRENT_LIABILITIES,
        0.95
    ),

    # 17. Short-Term Provisions
    (
        r"(provision\s*for\s*tax|prov(ision)?\s*for\s*income\s*tax|provision\s*for\s*audit|audit\s*fees\s*payable)",
        ICAIGroup.SHORT_TERM_PROVISIONS,
        0.90
    ),

    # 18. Revenue from Operations
    (
        r"(sales\s*revenue|sales|revenue\s*from\s*operations|gross\s*receipts|service\s*revenue|professional\s*fees|consulting\s*income|job\s*work\s*income)",
        ICAIGroup.REVENUE_OPERATIONS,
        0.95
    ),

    # 19. Other Income
    (
        r"(interest\s*income|dividend\s*income|discount\s*received|commission\s*income|profit\s*on\s*sale|scrap\s*sales|miscellaneous\s*income|other\s*income)",
        ICAIGroup.OTHER_INCOME,
        0.92
    ),

    # 20. Cost of Materials Consumed / Purchases / COGS
    (
        r"(cost\s*of\s*goods\s*sold|cogs|purchase(s)?\s*of\s*stock|raw\s*material\s*consumed|material\s*cost|direct\s*expenses|freight\s*inward)",
        ICAIGroup.PURCHASES_STOCK_IN_TRADE,
        0.95
    ),

    # 21. Employee Benefits Expense
    (
        r"(salar(y|ies)\s*expense|salary|wages|staff\s*welfare|bonus|director\s*remuneration|partner\s*remuneration|pf\s*contribution|esic\s*contribution|gratuity\s*expense|staff\s*training)",
        ICAIGroup.EMPLOYEE_BENEFITS,
        0.95
    ),

    # 22. Finance Costs
    (
        r"(interest\s*expense|interest\s*on\s*loan|interest\s*on\s*borrowing|bank\s*charges|finance\s*charge(s)?|loan\s*processing\s*fee)",
        ICAIGroup.FINANCE_COSTS,
        0.95
    ),

    # 23. Depreciation & Amortisation Expense
    (
        r"(depreciation\s*expense|depreciation|amorti[zs]ation(\s*expense)?)",
        ICAIGroup.DEPRECIATION_AMORTISATION,
        0.95
    ),

    # 24. Other Expenses
    (
        r"(rent\s*expense|rent|office\s*supplies|utilities|electricity\s*expense|water\s*charges|insurance|legal\s*(&|and)?\s*professional|audit\s*fee(s)?|travelling|conveyance|repair(s)?\s*(&|and)?\s*maintenance|printing\s*(&|and)?\s*stationery|telephone|internet|advertis(ing|ement)|marketing|freight\s*outward|bad\s*debts|miscellaneous\s*expense|general\s*expense)",
        ICAIGroup.OTHER_EXPENSES,
        0.90
    ),

    # 25. Tax Expense
    (
        r"(income\s*tax\s*expense|current\s*tax|tax\s*provision\s*expense)",
        ICAIGroup.TAX_EXPENSE,
        0.90
    )
]

def classify_ledger(name: str, original_group: str = "", debit: float = 0.0, credit: float = 0.0) -> Tuple[ICAIGroup, float]:
    """Classifies a ledger account name and metadata into an ICAI Schedule III group."""
    clean_text = f"{name} {original_group}".strip().lower()
    
    # 1. Specific checks based on regex priority
    for pattern, group, confidence in RULES:
        if re.search(pattern, clean_text, re.IGNORECASE):
            return group, confidence
            
    # 2. Fallbacks based on original group hints or balance nature
    orig = original_group.lower()
    if any(k in orig for k in ["fixed asset", "property", "equipment"]):
        return ICAIGroup.PPE_GROSS, 0.75
    if any(k in orig for k in ["bank", "cash"]):
        return ICAIGroup.CASH_BANK_BALANCES, 0.80
    if any(k in orig for k in ["debtor", "receivable"]):
        return ICAIGroup.TRADE_RECEIVABLES, 0.80
    if any(k in orig for k in ["creditor", "payable"]):
        return ICAIGroup.TRADE_PAYABLES, 0.80
    if any(k in orig for k in ["sale", "revenue", "income", "turnover"]):
        return ICAIGroup.REVENUE_OPERATIONS if credit > 0 else ICAIGroup.OTHER_INCOME, 0.70
    if any(k in orig for k in ["expense", "indirect exp", "admin exp"]):
        return ICAIGroup.OTHER_EXPENSES, 0.70
    if any(k in orig for k in ["capital", "equity", "owner"]):
        return ICAIGroup.OWNERS_CAPITAL, 0.75
    if any(k in orig for k in ["loan", "borrowing", "liability"]):
        return ICAIGroup.LONG_TERM_BORROWINGS if credit > 0 else ICAIGroup.SHORT_TERM_LOANS_ADVANCES, 0.65

    # 3. Default fallback based on balance side
    if debit > 0 and credit == 0:
        return ICAIGroup.OTHER_EXPENSES, 0.40
    elif credit > 0 and debit == 0:
        return ICAIGroup.OTHER_INCOME, 0.40

    return ICAIGroup.UNMAPPED, 0.10
