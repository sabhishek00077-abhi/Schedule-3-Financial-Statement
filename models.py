"""Data models and ICAI Non-Corporate Schedule III classification heads."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

class ICAIGroup(str, Enum):
    # --- EQUITY AND LIABILITIES ---
    # 1. Owners' Funds
    OWNERS_CAPITAL = "OWNERS_CAPITAL"                     # Partner / Owner Capital, Drawings
    RESERVES_SURPLUS = "RESERVES_SURPLUS"                 # Reserves, Retained Earnings, Current Year Profit

    # 2. Non-Current Liabilities
    LONG_TERM_BORROWINGS = "LONG_TERM_BORROWINGS"         # Term Loans, Secured/Unsecured Loans
    DEFERRED_TAX_LIABILITY = "DEFERRED_TAX_LIABILITY"     # Deferred Tax Liability (Net)
    OTHER_LONG_TERM_LIABILITIES = "OTHER_LONG_TERM_LIABILITIES" # Long-term deposits, retentions
    LONG_TERM_PROVISIONS = "LONG_TERM_PROVISIONS"         # Gratuity, Leave Encashment

    # 3. Current Liabilities
    SHORT_TERM_BORROWINGS = "SHORT_TERM_BORROWINGS"       # CC/OD Limits, Short term bank loans
    TRADE_PAYABLES = "TRADE_PAYABLES"                     # Sundry Creditors, Bills Payable
    OTHER_CURRENT_LIABILITIES = "OTHER_CURRENT_LIABILITIES" # Outstanding Expenses, Taxes, Interest Payable
    SHORT_TERM_PROVISIONS = "SHORT_TERM_PROVISIONS"       # Provision for Tax, Audit Fee

    # --- ASSETS ---
    # 1. Non-Current Assets
    PPE_GROSS = "PPE_GROSS"                               # Property, Plant & Equipment (Gross)
    PPE_ACC_DEP = "PPE_ACC_DEP"                           # Accumulated Depreciation (Contra)
    INTANGIBLE_ASSETS = "INTANGIBLE_ASSETS"               # Goodwill, Software, Patents
    NON_CURRENT_INVESTMENTS = "NON_CURRENT_INVESTMENTS"   # Long-term investments
    DEFERRED_TAX_ASSET = "DEFERRED_TAX_ASSET"             # Deferred Tax Asset (Net)
    LONG_TERM_LOANS_ADVANCES = "LONG_TERM_LOANS_ADVANCES" # Security deposits, Capital advances
    OTHER_NON_CURRENT_ASSETS = "OTHER_NON_CURRENT_ASSETS" # Fixed deposits > 12m

    # 2. Current Assets
    CURRENT_INVESTMENTS = "CURRENT_INVESTMENTS"           # Liquid mutual funds, T-bills
    INVENTORIES = "INVENTORIES"                           # Raw materials, WIP, Stock-in-trade
    TRADE_RECEIVABLES = "TRADE_RECEIVABLES"               # Sundry Debtors, Bills Receivable
    CASH_BANK_BALANCES = "CASH_BANK_BALANCES"             # Cash in hand, Bank balances
    SHORT_TERM_LOANS_ADVANCES = "SHORT_TERM_LOANS_ADVANCES" # Prepaid expenses, GST credits, Advances
    OTHER_CURRENT_ASSETS = "OTHER_CURRENT_ASSETS"         # Accrued interest, other receivables

    # --- STATEMENT OF PROFIT AND LOSS ---
    # Income
    REVENUE_OPERATIONS = "REVENUE_OPERATIONS"             # Sales, Gross Receipts, Service Income
    OTHER_INCOME = "OTHER_INCOME"                         # Interest income, discounts, scrap sales

    # Expenses
    COST_OF_MATERIALS = "COST_OF_MATERIALS"               # Raw material consumed
    PURCHASES_STOCK_IN_TRADE = "PURCHASES_STOCK_IN_TRADE" # Purchases of trading goods / COGS
    CHANGES_INVENTORIES = "CHANGES_INVENTORIES"           # (Opening Stock - Closing Stock)
    EMPLOYEE_BENEFITS = "EMPLOYEE_BENEFITS"               # Salaries, wages, PF, partner remuneration
    FINANCE_COSTS = "FINANCE_COSTS"                       # Interest expense, bank charges
    DEPRECIATION_AMORTISATION = "DEPRECIATION_AMORTISATION" # Depreciation & amortisation
    OTHER_EXPENSES = "OTHER_EXPENSES"                     # Rent, rates, insurance, utilities, admin
    TAX_EXPENSE = "TAX_EXPENSE"                           # Current & deferred tax provisions

    # Fallback / Unmapped
    UNMAPPED = "UNMAPPED"

ICAI_GROUP_LABELS = {
    ICAIGroup.OWNERS_CAPITAL: "Owners' / Partners' Capital Accounts",
    ICAIGroup.RESERVES_SURPLUS: "Reserves and Surplus",
    ICAIGroup.LONG_TERM_BORROWINGS: "Long-Term Borrowings",
    ICAIGroup.DEFERRED_TAX_LIABILITY: "Deferred Tax Liabilities (Net)",
    ICAIGroup.OTHER_LONG_TERM_LIABILITIES: "Other Long-Term Liabilities",
    ICAIGroup.LONG_TERM_PROVISIONS: "Long-Term Provisions",
    ICAIGroup.SHORT_TERM_BORROWINGS: "Short-Term Borrowings",
    ICAIGroup.TRADE_PAYABLES: "Trade Payables",
    ICAIGroup.OTHER_CURRENT_LIABILITIES: "Other Current Liabilities",
    ICAIGroup.SHORT_TERM_PROVISIONS: "Short-Term Provisions",
    
    ICAIGroup.PPE_GROSS: "Property, Plant & Equipment (Gross)",
    ICAIGroup.PPE_ACC_DEP: "Less: Accumulated Depreciation",
    ICAIGroup.INTANGIBLE_ASSETS: "Intangible Assets",
    ICAIGroup.NON_CURRENT_INVESTMENTS: "Non-Current Investments",
    ICAIGroup.DEFERRED_TAX_ASSET: "Deferred Tax Assets (Net)",
    ICAIGroup.LONG_TERM_LOANS_ADVANCES: "Long-Term Loans and Advances",
    ICAIGroup.OTHER_NON_CURRENT_ASSETS: "Other Non-Current Assets",
    ICAIGroup.CURRENT_INVESTMENTS: "Current Investments",
    ICAIGroup.INVENTORIES: "Inventories",
    ICAIGroup.TRADE_RECEIVABLES: "Trade Receivables",
    ICAIGroup.CASH_BANK_BALANCES: "Cash and Bank Balances",
    ICAIGroup.SHORT_TERM_LOANS_ADVANCES: "Short-Term Loans and Advances",
    ICAIGroup.OTHER_CURRENT_ASSETS: "Other Current Assets",
    
    ICAIGroup.REVENUE_OPERATIONS: "Revenue from Operations",
    ICAIGroup.OTHER_INCOME: "Other Income",
    ICAIGroup.COST_OF_MATERIALS: "Cost of Materials Consumed",
    ICAIGroup.PURCHASES_STOCK_IN_TRADE: "Purchases of Stock-in-Trade / COGS",
    ICAIGroup.CHANGES_INVENTORIES: "Changes in Inventories (FG, WIP, Stock-in-Trade)",
    ICAIGroup.EMPLOYEE_BENEFITS: "Employee Benefits Expense",
    ICAIGroup.FINANCE_COSTS: "Finance Costs",
    ICAIGroup.DEPRECIATION_AMORTISATION: "Depreciation and Amortisation Expense",
    ICAIGroup.OTHER_EXPENSES: "Other Expenses",
    ICAIGroup.TAX_EXPENSE: "Tax Expense",
    ICAIGroup.UNMAPPED: "Unmapped / To Be Reviewed"
}

@dataclass
class RawLedgerItem:
    id: str
    name: str
    code: str = ""
    debit: float = 0.0
    credit: float = 0.0
    original_group: str = ""
    assigned_group: ICAIGroup = ICAIGroup.UNMAPPED
    confidence: float = 0.0
    notes: str = ""

@dataclass
class EntityInfo:
    name: str = "Shree Balaji Enterprises"
    entity_type: str = "Partnership Firm" # Sole Proprietorship / Partnership Firm / LLP / AOP
    financial_year: str = "2025-2026"
    as_on_date: str = "31st March 2026"
    currency_symbol: str = "₹"
    round_off: str = "Actuals" # Actuals / In Thousands / In Lakhs

@dataclass
class NoteItem:
    note_number: int
    title: str
    group_key: str
    items: List[Dict[str, Any]] = field(default_factory=list)
    total_current_year: float = 0.0
    total_previous_year: float = 0.0

@dataclass
class StatementRow:
    particulars: str
    note_no: Optional[str] = None
    amount_current_year: float = 0.0
    amount_previous_year: float = 0.0
    is_header: bool = False
    is_total: bool = False
    is_sub_header: bool = False
    indent_level: int = 0
