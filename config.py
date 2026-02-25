"""
Configuration module for banking report analysis.

This module contains constants, thresholds, and mapping dictionaries
for bank accounting codes used in financial statements parsing.
"""

from typing import Dict, List, Tuple


# Bank account codes mapping - Russian banking chart of accounts (COA)
BANK_ACCOUNT_CODES: Dict[str, str] = {
    # Assets
    "10101": "Касса кредитной организации",
    "10202": "Денежные средства в Банке России",
    "10203": "Денежные средства в кредитных организациях",
    "10302": "Средства в Банке России на correspondent'ских счетах",
    "10303": "Средства в кредитных организациях на correspondent'ских счетах",
    "10501": "Драгоценные металлы",
    "10601": "Драгоценные камни",
    "10801": "Собственные акции, выкупленные у акционеров",
    "10901": "Незавершенные строительные проекты",
    "11001": "Материалы",
    "11501": "Долговые ценные бумаги",
    "11502": "Долговые ценные бумаги, приобретенные для торговли",
    "11503": "Долговые ценные бумаги, предназначенные для продажи",
    "11504": "Долговые ценные бумаги, предназначенные для удержания до погашения",
    "11505": "Долговые ценные бумаги, предназначенные для продажи по справедливой стоимости",
    "11601": "Кредиты, предоставленные юридическим лицам",
    "11602": "Кредиты, предоставленные физическим лицам",
    "11603": "Кредиты, предоставленные бюджетным организациям",
    "11701": "Основные средства",
    "11801": "Нематериальные активы",
    "11901": "Отложенные налоговые активы",
    
    # Liabilities
    "20202": "Депозиты физических лиц",
    "20203": "Депозиты юридических лиц",
    "20204": "Депозиты бюджетных организаций",
    "20301": "Средства клиентов (депонентов)",
    "20501": "Кредиты, полученные от Банка России",
    "20502": "Кредиты, полученные от кредитных организаций",
    "20601": "Выпущенные облигации",
    "20801": "Уставный капитал",
    "20901": "Добавочный капитал",
    "21001": "Резервы под обесценение активов",
    "21101": "Нераспределенная прибыль (непокрытый убыток)",
    
    # Income Statement accounts
    "70601": "Процентные доходы",
    "70602": "Процентные расходы",
    "70701": "Комиссионные доходы",
    "70702": "Комиссионные расходы",
    "71101": "Доходы от операций с ценными бумагами",
    "71102": "Расходы от операций с ценными бумагами",
    "71501": "Доходы от участия в других организациях",
    "71601": "Внереализационные доходы",
    "71602": "Внереализационные расходы",
    "72501": "Расходы на оплату труда",
    "72601": "Отчисления на социальное страхование и обеспечение",
    "72701": "Амортизация",
    "73101": "Прочие операционные расходы",
    "73201": "Резервы под обесценение ценных бумаг",
    "73301": "Резервы под обесценение долговых требований",
    "73401": "Резервы под возможные потери по обязательствам",
    "73501": "Налог на прибыль"
}


# Balance sheet key items mapping for simplified identification
BALANCE_SHEET_ITEMS: Dict[str, List[str]] = {
    "total_assets": ["11000", "11100", "11200", "11300", "11400", "11500", "11600", "11700", "11800", "11900"],
    "total_liabilities": ["21000", "21100", "21200", "21300", "21400", "21500", "21600", "21700", "21800", "21900"],
    "equity": ["20801", "20901", "21001", "21101"],
    "cash_and_equivalents": ["10101", "10202", "10302"],
    "loans_to_customers": ["11601", "11602", "11603"],
    "deposits_from_customers": ["20202", "20203", "20204", "20301"]
}

# Digital banking indicators mapping
DIGITAL_BANKING_INDICATORS: Dict[str, List[str]] = {
    "number_corporate_online_banking_customers": [
        "Количество корпоративных клиентов интернет-банка", 
        "Число корпоративных клиентов онлайн-банкинга",
        "Corporate Online Banking Users",
        "Number of Corporate Online Banking Customers"
    ],
    "number_personal_online_banking_customers": [
        "Количество частных клиентов интернет-банка", 
        "Число частных клиентов онлайн-банкинга",
        "Personal Online Banking Users",
        "Number of Personal Online Banking Customers"
    ],
    "number_mobile_banking_customers": [
        "Количество пользователей мобильного банкинга",
        "Mobile Banking Users",
        "Number of Mobile Banking Customers"
    ],
    "number_telephone_banking_customers": [
        "Количество клиентов телефонного банкинга",
        "Telephone Banking Users",
        "Number of Telephone Banking Customers"
    ],
    "transaction_amount_corporate_online_banking": [
        "Объем транзакций корпоративного онлайн-банкинга",
        "Transaction amount of corporate online banking"
    ],
    "transaction_amount_personal_online_banking": [
        "Объем транзакций частного онлайн-банкинга",
        "Transaction amount of personal online banking"
    ],
    "transaction_amount_mobile_banking": [
        "Объем транзакций мобильного банкинга",
        "Transaction amount of mobile banking"
    ],
    "transaction_amount_self_service_banking": [
        "Объем транзакций через устройства самообслуживания",
        "Transaction amount of self-service banking"
    ],
    "ebanking_transaction_volume": [
        "Объем электронных транзакций",
        "Bank's e-banking transaction volume reached"
    ],
    "ebanking_substitution_ratio": [
        "Доля электронных каналов в общем количестве операций",
        "The substitution ratio of e-banking channels for traditional"
    ],
    "customer_satisfaction_level": [
        "Уровень удовлетворенности клиентов",
        "Customer satisfaction level"
    ],
    "number_mobile_cash_agents": [
        "Количество агентов мобильного снятия наличных",
        "the number of mobile cash withdrawal agents"
    ],
    "monthly_active_mobile_banking_customers": [
        "Количество активных пользователей мобильного банка в месяц",
        "Monthly active mobile banking customers"
    ]
}

# Financial performance indicators mapping
FINANCIAL_PERFORMANCE_INDICATORS: Dict[str, List[str]] = {
    "operating_income": [
        "Выручка от основной деятельности",
        "Operating income",
        "Operating income (RMB Million)"
    ],
    "operating_profit": [
        "Операционная прибыль", 
        "Operating profit",
        "Operating profit (RMB Million)"
    ],
    "profit_for_the_year": [
        "Прибыль за год",
        "Profit for the year",
        "Profit for the year (RMB Million)"
    ],
    "eps_basic": [
        "EPS (базовая)",
        "EPS (basic) (RMB)"
    ],
    "roa": [
        "ROA (%)",
        "Return on Assets (%)"
    ],
    "roe": [
        "ROE (%)",
        "Return on Equity (%)"
    ],
    "net_interest_margin": [
        "Чистая процентная маржа (%)",
        "Net interest margin (%)"
    ],
    "cost_to_income_ratio": [
        "Соотношение расходов к доходам (%)",
        "Cost to income (calculated under domestic regulations) (%)"
    ],
    "non_interest_income_ratio": [
        "Доля прочих доходов в операционных доходах (%)",
        "Non-interest income to operating income (%)"
    ],
    "credit_cost": [
        "Кредитные издержки (%)",
        "Credit cost (%)"
    ],
    "non_performing_loan_ratio": [
        "Доля просроченных кредитов (%)",
        "Non-performing loans to total loans (%)"
    ],
    "loan_loss_provision_coverage": [
        "Покрытие просроченных кредитов резервами (%)",
        "Allowance for loan impairment losses to non-performing loans (%)"
    ],
    "total_deposits": [
        "Общие депозиты",
        "Total Deposits"
    ],
    "total_loans": [
        "Общие кредиты",
        "Total Loan"
    ],
    "non_performing_loans_balance": [
        "Баланс просроченных кредитов",
        "Balance of Non-performing Loans"
    ],
    "interest_earning_assets": [
        "Процентные активы",
        "Interest-earning Assets"
    ],
    "interest_bearing_liabilities": [
        "Процентные обязательства",
        "Interest-bearing Liabilities"
    ],
    "net_interest_spread": [
        "Процентный спред",
        "Net Interest Spread"
    ],
    "net_interest_margin_detailed": [
        "Чистая процентная маржа (подробно)",
        "Net Interest Margin"
    ],
    "interbank_assets": [
        "Межбанковские активы",
        "Interbank Assets"
    ],
    "interbank_liabilities": [
        "Межбанковские обязательства",
        "Interbank Liabilities"
    ],
    "equity_to_debt_ratio": [
        "Соотношение собственного капитала к заемному",
        "Ratio of Equity to Debt"
    ],
    "retained_earnings_to_total_assets": [
        "Соотношение нераспределенной прибыли к активам",
        "Ratio of Retained Earnings to Total Assets"
    ],
    "ebit_to_total_assets": [
        "Соотношение прибыли до вычета процентов и налогов к активам",
        "Ratio of Earnings before Interest And Taxes to Total Assets"
    ],
    "total_assets_turnover": [
        "Оборачиваемость активов",
        "Total Assets Turnover"
    ],
    "return_on_net_assets": [
        "Рентабельность чистых активов",
        "Weighted Average Return on Net Assets"
    ],
    "return_on_average_total_assets": [
        "Рентабельность средних активов",
        "Return on Average Total Assets"
    ],
    "return_on_net_assets_after_deducting_non_recurring": [
        "Рентабельность чистых активов после исключения разовых факторов",
        "Weighted Average Return on Net Assets after Deducting Non-Recurring Profit and Loss"
    ],
    "interbank_assets_to_interest_earning_assets": [
        "Соотношение межбанковских активов к процентным активам",
        "Ratio of Interbank Assets to Interest-earning Assets"
    ],
    "deposits_to_interest_bearing_liabilities": [
        "Соотношение депозитов к процентным обязательствам",
        "Ratio of Deposits to Interest-bearing Liabilities"
    ],
    "interbank_liabilities_to_interest_bearing_liabilities": [
        "Соотношение межбанковских обязательств к процентным обязательствам",
        "Ratio of Interbank Liabilities to Interest-bearing Liabilities"
    ]
}


# Key performance indicators thresholds
RATIOS_THRESHOLDS: Dict[str, Tuple[float, float]] = {
    # Capital Adequacy (Basel III simplified)
    "capital_adequacy": (0.08, 0.12),  # Min 8%, Ideal 12%
    
    # Liquidity ratios
    "instant_liquidity": (0.15, 0.25),  # Min 15%, Ideal 25% 
    "current_liquidity": (1.0, 1.5),    # Min 1.0, Ideal 1.5
    
    # Profitability ratios
    "roe": (0.10, 0.15),                # Min 10%, Ideal 15%
    "roa": (0.01, 0.02),                # Min 1%, Ideal 2%
    "nim": (0.02, 0.04),                # Min 2%, Ideal 4%
    
    # Asset quality ratio
    "problem_loans_ratio": (0.05, 0.02) # Max 5%, Ideal 2% (reverse threshold)
}


# Financial statement sections identifiers
STATEMENT_SECTIONS: List[str] = [
    "balance_sheet",           # Balance Sheet
    "income_statement",       # Profit and Loss Statement
    "cash_flow",             # Cash Flow Statement
    "statement_of_changes_in_equity"  # Statement of Changes in Equity
]


# Supported file formats
SUPPORTED_FORMATS: List[str] = [
    ".pdf", ".docx", ".txt", ".md"
]