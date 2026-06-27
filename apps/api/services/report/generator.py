from typing import List, Dict, Any

def generate_html_report(session_id: str, summary: Dict[str, Any], transactions: List[Any], insights: List[Dict[str, Any]]) -> str:
    """
    Compiles session summary data, transactions, and insights into a beautifully styled,
    standalone HTML document optimized for printing and PDF export.
    """
    
    # Formatter helpers
    def fmt_currency(val: float) -> str:
        return f"₹{val:,.2f}"

    def fmt_currency_no_decimal(val: float) -> str:
        return f"₹{val:,.0f}"

    # Extract metrics
    income = summary.get("income", 0.0)
    spend = summary.get("spend", 0.0)
    savings = summary.get("savings", 0.0)
    savings_rate = summary.get("savingsRate", 0.0)
    recurring_total = summary.get("recurringTotal", 0.0)
    top_categories = summary.get("topCategories", [])
    biggest_tx = summary.get("biggestTransaction")

    # Render category rows
    category_rows_html = ""
    for cat in top_categories:
        category_rows_html += f"""
        <tr>
            <td style="padding: 10px 12px; font-weight: 600; color: #1f2937;">{cat['category']}</td>
            <td style="padding: 10px 12px; text-align: right; color: #374151;">{fmt_currency(cat['amount'])}</td>
            <td style="padding: 10px 12px; text-align: right; font-weight: 700; color: #10b981;">{cat['percentage']}%</td>
        </tr>
        """

    # Render insights list HTML
    insights_html = ""
    for ins in insights:
        # Style depending on type / score
        border_color = "#e5e7eb"
        if ins.get("relevance", 0) >= 0.85:
            border_color = "#f87171"  # red
        elif ins.get("type") == "savings_rate" and ins.get("id") == "insight_savings_healthy":
            border_color = "#34d399"  # green
        
        insights_html += f"""
        <div style="border-left: 4px solid {border_color}; background-color: #f9fafb; padding: 14px 18px; border-radius: 6px; margin-bottom: 12px;">
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 4px;">
                <tr>
                    <td style="font-size: 11px; text-transform: uppercase; font-weight: 800; color: #6b7280; letter-spacing: 0.05em; text-align: left; padding: 0;">
                        {ins.get('type', 'INSIGHT').replace('_', ' ')}
                    </td>
                    <td style="font-size: 10px; color: #9ca3af; text-align: right; padding: 0;">
                        Relevance: {ins.get('relevance', 0.5):.2f}
                    </td>
                </tr>
            </table>
            <h4 style="margin: 0 0 6px 0; font-size: 14px; font-weight: 700; color: #111827;">{ins['title']}</h4>
            <p style="margin: 0; font-size: 12px; color: #4b5563; line-height: 1.5;">{ins['text']}</p>
        </div>
        """

    # Render transactions rows
    tx_rows_html = ""
    for tx in transactions:
        # Access attributes safely
        date = getattr(tx, "date", tx.get("date") if isinstance(tx, dict) else "")
        desc = getattr(tx, "clean_description", tx.get("cleanDescription") if isinstance(tx, dict) else "")
        raw_desc = getattr(tx, "raw_description", tx.get("rawDescription") if isinstance(tx, dict) else "")
        category = getattr(tx, "category", tx.get("category") if isinstance(tx, dict) else "Other")
        amount = getattr(tx, "amount", tx.get("amount") if isinstance(tx, dict) else 0.0)
        tx_type = getattr(tx, "type", tx.get("type") if isinstance(tx, dict) else "debit")
        
        is_debit = tx_type == "debit"
        amt_class = "color: #dc2626;" if is_debit else "color: #16a34a;"
        sign = "-" if is_debit else ""
        
        tx_rows_html += f"""
        <tr style="border-bottom: 1px solid #f3f4f6;">
            <td style="padding: 10px 12px; color: #4b5563; font-family: monospace; white-space: nowrap;">{date}</td>
            <td style="padding: 10px 12px;">
                <div style="font-weight: 600; color: #1f2937;">{desc}</div>
                <div style="font-size: 9px; color: #9ca3af; font-family: monospace; margin-top: 2px;">{raw_desc}</div>
            </td>
            <td style="padding: 10px 12px;">
                <span style="font-size: 10px; font-weight: 600; padding: 2px 6px; background-color: #f3f4f6; color: #4b5563; border-radius: 4px; border: 1px solid #e5e7eb;">
                    {category}
                </span>
            </td>
            <td style="padding: 10px 12px; text-align: right; font-weight: 700; {amt_class}">
                {sign}{fmt_currency(abs(amount))}
              </td>
        </tr>
        """

    # Assemble HTML page
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>RupeeRadar Financial Report — {session_id[:8]}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #ffffff;
            color: #111827;
            margin: 0;
            padding: 40px 20px;
            line-height: 1.4;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .title {{
            font-size: 24px;
            font-weight: 800;
            background: linear-gradient(to right, #10b981, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
        }}
        .subtitle {{
            font-size: 11px;
            text-transform: uppercase;
            font-weight: 700;
            color: #6b7280;
            margin-top: 4px;
            letter-spacing: 0.1em;
        }}
        .meta {{
            text-align: right;
            font-size: 12px;
            color: #4b5563;
        }}
        .grid-kpis {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}
        .kpi-card {{
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 12px 16px;
            background-color: #fafafa;
        }}
        .kpi-label {{
            font-size: 10px;
            text-transform: uppercase;
            font-weight: 700;
            color: #6b7280;
            letter-spacing: 0.05em;
        }}
        .kpi-val {{
            font-size: 16px;
            font-weight: 800;
            margin-top: 4px;
            color: #1f2937;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 800;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 8px;
            margin-top: 30px;
            margin-bottom: 15px;
            color: #111827;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .table-report {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-bottom: 20px;
        }}
        .table-report th {{
            background-color: #f9fafb;
            padding: 10px 12px;
            font-weight: 700;
            color: #4b5563;
            border-bottom: 1px solid #e5e7eb;
            text-transform: uppercase;
            font-size: 10px;
            letter-spacing: 0.05em;
        }}
        @media print {{
            body {{
                padding: 0;
            }}
            .no-print {{
                display: none;
            }}
            .page-break {{
                page-break-before: always;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Control bar (hidden during print) -->
        <div class="no-print" style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; background-color: #f3f4f6; padding: 10px 15px; border-radius: 8px;">
            <span style="font-size: 12px; color: #4b5563; font-weight: 500;">rupeeradar print console</span>
            <button onclick="window.print()" style="background-color: #10b981; color: white; border: none; padding: 6px 16px; border-radius: 6px; font-size: 12px; font-weight: 700; cursor: pointer;">
                Save as PDF / Print
            </button>
        </div>

        <!-- Header -->
        <div class="header">
            <div>
                <h1 class="title">RupeeRadar</h1>
                <div class="subtitle">Personal Finance Assistant Report</div>
            </div>
            <div class="meta">
                <div><strong>Session ID:</strong> {session_id}</div>
                <div><strong>Format:</strong> HTML Export</div>
            </div>
        </div>

        <!-- KPI metrics -->
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px; table-layout: fixed;">
            <tr>
                <td style="width: 20%; padding-right: 8px;">
                    <div class="kpi-card">
                        <div class="kpi-label">Income</div>
                        <div class="kpi-val" style="color: #10b981;">{fmt_currency_no_decimal(income)}</div>
                    </div>
                </td>
                <td style="width: 20%; padding: 0 8px;">
                    <div class="kpi-card">
                        <div class="kpi-label">Spend</div>
                        <div class="kpi-val" style="color: #ef4444;">{fmt_currency_no_decimal(spend)}</div>
                    </div>
                </td>
                <td style="width: 20%; padding: 0 8px;">
                    <div class="kpi-card">
                        <div class="kpi-label">Net Savings</div>
                        <div class="kpi-val" style="color: { '#06b6d4' if savings >= 0 else '#ef4444' };">{fmt_currency_no_decimal(savings)}</div>
                    </div>
                </td>
                <td style="width: 20%; padding: 0 8px;">
                    <div class="kpi-card">
                        <div class="kpi-label">Savings Rate</div>
                        <div class="kpi-val">{savings_rate}%</div>
                    </div>
                </td>
                <td style="width: 20%; padding-left: 8px;">
                    <div class="kpi-card">
                        <div class="kpi-label">Recurring</div>
                        <div class="kpi-val">{fmt_currency_no_decimal(recurring_total)}</div>
                    </div>
                </td>
            </tr>
        </table>

        <!-- Main Content (2-Column Layout) -->
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; table-layout: fixed;">
            <tr>
                <!-- Left Column: Categories -->
                <td style="width: 48%; vertical-align: top; padding-right: 15px;">
                    <div class="section-title">Spend by Category</div>
                    <table class="table-report">
                        <thead>
                            <tr>
                                <th style="text-align: left;">Category</th>
                                <th style="text-align: right;">Amount</th>
                                <th style="text-align: right;">% of Spend</th>
                            </tr>
                        </thead>
                        <tbody>
                            {category_rows_html}
                        </tbody>
                    </table>
                    
                    {f'''
                    <div class="section-title">Largest Single Expense</div>
                    <div style="border: 1px dashed #e5e7eb; border-radius: 6px; padding: 12px; font-size: 12px; background-color: #fafafa;">
                        <div style="font-weight: 700; color: #111827;">{biggest_tx['description']}</div>
                        <div style="margin-top: 4px; color: #4b5563;">
                            <span>Date: {biggest_tx['date']}</span> | 
                            <span>Category: {biggest_tx['category']}</span>
                        </div>
                        <div style="font-size: 16px; font-weight: 800; color: #dc2626; margin-top: 6px;">
                            {fmt_currency(abs(biggest_tx['amount']))}
                        </div>
                    </div>
                    ''' if biggest_tx else ''}
                </td>
                <!-- Spacing column -->
                <td style="width: 4%;"></td>
                <!-- Right Column: Insights -->
                <td style="width: 48%; vertical-align: top; padding-left: 15px;">
                    <div class="section-title">Financial Behavior Insights</div>
                    <div>
                        {insights_html}
                    </div>
                </td>
            </tr>
        </table>

        <!-- Page break for full transaction ledger in PDF -->
        <div class="page-break"></div>
        
        <!-- Transaction ledger list -->
        <div class="section-title">Transactions Ledger</div>
        <table class="table-report" style="width: 100%; text-align: left;">
            <thead>
                <tr>
                    <th style="text-align: left; width: 10%;">Date</th>
                    <th style="text-align: left; width: 55%;">Description</th>
                    <th style="text-align: left; width: 15%;">Category</th>
                    <th style="text-align: right; width: 20%;">Amount</th>
                </tr>
            </thead>
            <tbody>
                {tx_rows_html}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    return html

def generate_pdf_report(html_content: str) -> bytes:
    """
    Converts compiled HTML report content into a PDF document byte string using xhtml2pdf.
    """
    import io
    import re
    from xhtml2pdf import pisa
    
    # 1. Remove print console control bar from PDF output
    html_content = re.sub(
        r'<!-- Control bar .*?-->\s*<div class="no-print".*?</div>\s*</div>', 
        '', 
        html_content, 
        flags=re.DOTALL
    )
    
    # 2. Replace format metadata text to reflect PDF format
    html_content = html_content.replace(
        '<div><strong>Format:</strong> HTML Export</div>',
        '<div><strong>Format:</strong> PDF Export</div>'
    )
    
    # 3. Replace Rupee symbol ₹ with Rs. to prevent black box glyph rendering in PDF
    html_content = html_content.replace('₹', 'Rs. ')
    
    # 4. Remove external Google fonts import to avoid network and file permission exceptions in ReportLab
    html_content = re.sub(
        r"@import url\('https://fonts.googleapis.com/css2\?family=Inter.*?'\);", 
        '', 
        html_content
    )
    
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
    if pisa_status.err:
        raise ValueError(f"Failed to generate PDF report: {pisa_status.err}")
    return pdf_buffer.getvalue()
