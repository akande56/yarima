# utils/receipt_generator.py
from weasyprint import HTML

def generate_receipt_pdf(html_string):
    """Convert HTML string to PDF bytes using WeasyPrint."""
    html = HTML(string=html_string)
    return html.write_pdf()