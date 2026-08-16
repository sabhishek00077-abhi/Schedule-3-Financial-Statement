"""Significant Accounting Policies & Draft Auditor's Report Generator."""
from typing import Dict, Any, List
from .models import EntityInfo

def generate_accounting_policies(entity: EntityInfo) -> List[Dict[str, str]]:
    """Generates standard Significant Accounting Policies as per ICAI Accounting Standards."""
    return [
        {
            "standard": "AS 1 — Disclosure of Accounting Policies",
            "title": "Basis of Preparation",
            "policy": f"The financial statements of {entity.name} have been prepared in accordance with Generally Accepted Accounting Principles in India (Indian GAAP) and the Technical Guide on Financial Statements of Non-Corporate Entities issued by the Institute of Chartered Accountants of India (ICAI). The entity adopts the historical cost convention on an accrual basis."
        },
        {
            "standard": "AS 2 — Valuation of Inventories",
            "title": "Inventories",
            "policy": "Inventories comprising raw materials, stock-in-trade, and finished goods are valued at lower of cost (computed on FIFO / Weighted Average basis) and net realizable value. Cost includes purchase cost, duties, taxes, and other direct expenses incurred in bringing the inventory to its present location and condition."
        },
        {
            "standard": "AS 9 — Revenue Recognition",
            "title": "Revenue Recognition",
            "policy": "Revenue from the sale of goods is recognized upon transfer of significant risks and rewards of ownership to the buyer, net of trade discounts, returns, and Goods and Services Tax (GST). Service revenue is recognized as and when services are rendered."
        },
        {
            "standard": "AS 10 — Property, Plant and Equipment",
            "title": "Property, Plant and Equipment (PPE) & Depreciation",
            "policy": "Property, plant and equipment are stated at cost of acquisition or construction less accumulated depreciation and impairment losses. Depreciation is provided systematically over the estimated useful life of the assets using the Straight Line Method (SLM) / Written Down Value (WDV) method."
        },
        {
            "standard": "AS 15 — Employee Benefits",
            "title": "Employee Benefits",
            "policy": "Short-term employee benefits such as salaries, wages, bonus, and leave benefits are recognized as an expense during the period in which the employee renders related service. Defined contributions (EPF, ESIC) are charged to the Statement of Profit and Loss."
        },
        {
            "standard": "AS 16 — Borrowing Costs",
            "title": "Borrowing Costs",
            "policy": "Borrowing costs directly attributable to the acquisition, construction, or production of qualifying assets are capitalized as part of the asset cost. Other finance and borrowing costs are expensed in the period in which they occur."
        },
        {
            "standard": "AS 22 — Taxes on Income",
            "title": "Taxes on Income",
            "policy": "Tax expense comprises current tax and deferred tax. Current tax is measured at the amount expected to be paid to the taxation authorities in accordance with the Income Tax Act, 1961. Deferred tax assets and liabilities are recognized for future tax consequences of timing differences."
        },
        {
            "standard": "AS 29 — Provisions and Contingencies",
            "title": "Provisions, Contingent Liabilities and Contingent Assets",
            "policy": "Provisions are recognized when the entity has a present legal or constructive obligation as a result of past events. Contingent liabilities are disclosed in the notes and not recognized in the balance sheet."
        }
    ]

def generate_draft_audit_report(entity: EntityInfo, is_balanced: bool, net_profit: float) -> Dict[str, Any]:
    """Generates a Draft Independent Auditor's Report as per ICAI Standards on Auditing (SA 700)."""
    return {
        "title": "INDEPENDENT AUDITOR'S REPORT",
        "addressee": f"To the Partners / Proprietor of {entity.name}",
        "opinion_type": "Unmodified Opinion (True and Fair View)" if is_balanced else "Qualified / Disclaimer of Opinion",
        "opinion_text": (
            f"In our opinion and to the best of our information and according to the explanations given to us, "
            f"the aforesaid financial statements give a true and fair view in conformity with the accounting principles "
            f"generally accepted in India, of the state of affairs of {entity.name} as at {entity.as_on_date}, "
            f"and its Profit (amounting to ₹{net_profit:,.2f}) and its cash flows for the year ended on that date."
            if is_balanced else
            f"Due to significant differences in trial balance reconciliation, we do not express an unmodified opinion on the financial statements."
        ),
        "basis_for_opinion": (
            "We conducted our audit in accordance with the Standards on Auditing (SAs) issued by the Institute of Chartered Accountants of India (ICAI). "
            "We are independent of the entity in accordance with the Code of Ethics issued by the ICAI, and we have fulfilled our ethical responsibilities."
        ),
        "management_responsibility": (
            f"The Management / Partners of {entity.name} are responsible for the preparation of these financial statements "
            f"that give a true and fair view in accordance with the ICAI Technical Guide for Non-Corporate Entities, "
            f"including the design, implementation, and maintenance of internal controls relevant to the preparation and presentation of financial statements."
        ),
        "auditor_responsibility": (
            "Our objectives are to obtain reasonable assurance about whether the financial statements as a whole are free from material misstatement, "
            "whether due to fraud or error, and to issue an auditor's report that includes our opinion."
        ),
        "place": "Ahmedabad / Mumbai",
        "date": entity.as_on_date,
        "ca_firm": "KMS & Associates",
        "ca_name": "CA. Abhishek Shriwas, FCA",
        "membership_no": "184592",
        "firm_reg_no": "104928W",
        "udin": "26184592AAAAAB9281"
    }
