import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def generate_csv_fixture(path: str):
    data = [
        {"date": "2026-08-01", "description": "Grocery Store", "amount": "150.00", "type": "Groceries"},
        {"date": "2026-08-02", "description": "Gas Station", "amount": "40.00", "type": "Transport"},
        {"date": "2026-08-05", "description": "Online Shopping", "amount": "120.50", "type": "Shopping"},
    ]
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["date", "description", "amount", "type"])
        writer.writeheader()
        writer.writerows(data)
    print(f"Generated {path}")

def generate_pdf_fixture(path: str):
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Bank B Credit Card Statement")
    
    # Statement Summary
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, "Purchase Balance: 100,000.00")
    c.drawString(50, height - 120, "Purchase APR: 28.0%")
    c.drawString(50, height - 140, "Due Date: 2026-08-25")
    c.drawString(50, height - 160, "Minimum Payment: 5,000.00")
    
    # Transactions
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 200, "Transactions")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 230, "2026-08-01 Grocery Store 5000.00")
    c.drawString(50, height - 250, "2026-08-02 Electronics Shop 25000.00")
    c.drawString(50, height - 270, "2026-08-10 Restaurant 3000.00")
    
    c.save()
    print(f"Generated {path}")

if __name__ == "__main__":
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    os.makedirs(fixtures_dir, exist_ok=True)
    
    generate_csv_fixture(os.path.join(fixtures_dir, "sample_statement_bank_a.csv"))
    generate_pdf_fixture(os.path.join(fixtures_dir, "sample_statement_bank_b.pdf"))
