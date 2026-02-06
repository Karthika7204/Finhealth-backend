from fpdf import FPDF
import datetime

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Financial AI Report', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def safe_text(text):
    """
    Sanitize text to be compatible with FPDF's latin-1 encoding.
    Replaces unsupported characters (like emojis or rupee symbol) with '?'.
    """
    if not isinstance(text, str):
        text = str(text)
    return text.encode('latin-1', 'replace').decode('latin-1')

def generate_report_pdf(user, analysis):
    pdf = PDFReport()
    pdf.add_page()
    
    # --- Section 1: Company Details ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. Company Details', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    
    pdf.cell(40, 10, 'Business Name:', 0, 0)
    pdf.cell(0, 10, safe_text(user.business_name or 'N/A'), 0, 1)
    
    pdf.cell(40, 10, 'Email:', 0, 0)
    pdf.cell(0, 10, safe_text(user.email), 0, 1)
    
    pdf.cell(40, 10, 'Phone:', 0, 0)
    pdf.cell(0, 10, safe_text(user.phone_number or 'N/A'), 0, 1)
    
    pdf.cell(40, 10, 'Report Date:', 0, 0)
    pdf.cell(0, 10, analysis.created_at.strftime("%Y-%m-%d %H:%M:%S"), 0, 1)
    
    pdf.ln(10)

    # --- Section 2: Report Data (Metrics) ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. Financial Metrics', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    
    metrics = [
        ('Credit Score', str(analysis.credit_score)),
        ('Risk Level', analysis.risk_level.upper()),
        ('Confidence Score', f"{analysis.confidence_score}%"),
        ('Total Revenue', f"{analysis.total_revenue:,.2f}" if analysis.total_revenue else "N/A"),
        ('Total Expenses', f"{analysis.total_expenses:,.2f}" if analysis.total_expenses else "N/A"),
        ('Net Profit', f"{analysis.net_profit:,.2f}" if analysis.net_profit else "N/A"),
    ]
    
    for label, value in metrics:
        pdf.cell(50, 8, label + ':', 0, 0)
        pdf.cell(0, 8, safe_text(value), 0, 1)

    pdf.ln(10)
    
    # --- Section 3: AI Analysis Output ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '3. AI Analysis & Recommendations', 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    
    # Recommendations
    raw = analysis.raw_result
    if raw and 'recommendations' in raw:
        for idx, rec in enumerate(raw['recommendations'], 1):
            text = rec.get('text', '')
            # Multi-cell for long text
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(10, 8, f"{idx}.", 0, 0)
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 8, safe_text(text))
            pdf.ln(2)
            
    else:
        pdf.multi_cell(0, 10, "No detailed recommendations available.")

    # Return PDF string (latin-1) 
    return pdf.output(dest='S')
