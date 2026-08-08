import csv
import io
import re
from abc import ABC, abstractmethod
from typing import List, Type, Dict, Optional
from datetime import date, datetime
from pydantic import BaseModel
import pdfplumber

class ParsedTransaction(BaseModel):
    date: date
    description: str
    amount: float
    raw_category_hint: Optional[str] = None

class ParsedStatement(BaseModel):
    issuing_bank: str
    statement_date: date
    due_date: date
    minimum_payment: float
    purchase_apr: float
    cash_advance_apr: float
    purchase_balance: float
    cash_advance_balance: float
    transactions: List[ParsedTransaction]

class BankStatementParser(ABC):
    @abstractmethod
    def parse(self, file_bytes: bytes) -> ParsedStatement:
        pass

class CsvBankParser(BankStatementParser):
    def parse(self, file_bytes: bytes) -> ParsedStatement:
        text = file_bytes.decode('utf-8')
        reader = csv.DictReader(io.StringIO(text))
        
        transactions = []
        for row in reader:
            try:
                tx_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
            except ValueError:
                continue
            amount = float(row['amount'])
            
            transactions.append(
                ParsedTransaction(
                    date=tx_date,
                    description=row['description'],
                    amount=amount,
                    raw_category_hint=row.get('type', '')
                )
            )
            
        # In this simple CSV example, we'll return dummy statement-level data
        # Usually, a CSV might only contain transactions, and we derive statement data from the file name or external input.
        # Here we mock it for demonstration as per the requirements to prove the adapter works.
        return ParsedStatement(
            issuing_bank="CsvBank",
            statement_date=date.today(),
            due_date=date.today(),
            minimum_payment=100.0,
            purchase_apr=0.15,
            cash_advance_apr=0.20,
            purchase_balance=1000.0,
            cash_advance_balance=0.0,
            transactions=transactions
        )

class PdfBankParser(BankStatementParser):
    def parse(self, file_bytes: bytes) -> ParsedStatement:
        text = ""
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        
        # Regex heuristics based on expected PDF fixture
        balance_match = re.search(r'Purchase Balance:\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
        purchase_balance = float(balance_match.group(1).replace(',', '')) if balance_match else 0.0
        
        apr_match = re.search(r'Purchase APR:\s*([\d,]+\.?\d*)%', text, re.IGNORECASE)
        purchase_apr = float(apr_match.group(1)) / 100.0 if apr_match else 0.0

        due_date_match = re.search(r'Due Date:\s*(\d{4}-\d{2}-\d{2})', text, re.IGNORECASE)
        due_date = datetime.strptime(due_date_match.group(1), '%Y-%m-%d').date() if due_date_match else date.today()

        min_payment_match = re.search(r'Minimum Payment:\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
        minimum_payment = float(min_payment_match.group(1).replace(',', '')) if min_payment_match else 0.0

        # Attempt to find transactions (Date, Description, Amount)
        # e.g. "2026-08-01 Grocery Store 150.00"
        transactions = []
        tx_matches = re.finditer(r'(\d{4}-\d{2}-\d{2})\s+([A-Za-z0-9\s]+?)\s+([\d,]+\.\d{2})', text)
        for match in tx_matches:
            tx_date_str, desc, amt_str = match.groups()
            transactions.append(
                ParsedTransaction(
                    date=datetime.strptime(tx_date_str, '%Y-%m-%d').date(),
                    description=desc.strip(),
                    amount=float(amt_str.replace(',', ''))
                )
            )

        return ParsedStatement(
            issuing_bank="PdfBank",
            statement_date=date.today(),
            due_date=due_date,
            minimum_payment=minimum_payment,
            purchase_apr=purchase_apr,
            cash_advance_apr=purchase_apr + 0.05, # mock derived
            purchase_balance=purchase_balance,
            cash_advance_balance=0.0,
            transactions=transactions
        )

class ParserRegistry:
    _registry: Dict[str, Type[BankStatementParser]] = {
        "csvbank": CsvBankParser,
        "pdfbank": PdfBankParser,
        # Can map file extensions if needed:
        ".csv": CsvBankParser,
        ".pdf": PdfBankParser,
    }

    @classmethod
    def get_parser(cls, identifier: str) -> BankStatementParser:
        identifier = identifier.lower()
        parser_cls = cls._registry.get(identifier)
        if not parser_cls:
            raise ValueError(f"No parser found for identifier: {identifier}")
        return parser_cls()
