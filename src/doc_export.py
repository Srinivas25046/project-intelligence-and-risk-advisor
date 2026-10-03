import io
from docx import Document as DocxWriter


def build_documentation_docx(data: dict) -> bytes:
    doc = DocxWriter()
    doc.add_heading("Project Documentation", level=0)

    doc.add_heading("User Stories", level=1)
    for us in data.get("user_stories", []):
        p = doc.add_paragraph()
        p.add_run(f"As a {us.get('role', '')}, ").bold = True
        p.add_run(f"I want to {us.get('goal', '')} so that {us.get('benefit', '')}.")

    doc.add_heading("Risk Register", level=1)
    table = doc.add_table(rows=1, cols=5)
    table.style = "Light Grid Accent 1"
    for i, h in enumerate(["ID", "Description", "Severity", "Impact", "Mitigation Suggestion"]):
        table.rows[0].cells[i].text = h
    for r in data.get("risk_register", []):
        row = table.add_row().cells
        row[0].text = str(r.get("risk_id", ""))
        row[1].text = str(r.get("description", ""))
        row[2].text = str(r.get("severity", ""))
        row[3].text = str(r.get("impact", ""))
        row[4].text = str(r.get("mitigation_suggestion", ""))

    doc.add_heading("Action Item List", level=1)
    table2 = doc.add_table(rows=1, cols=4)
    table2.style = "Light Grid Accent 1"
    for i, h in enumerate(["Item", "Owner", "Status", "Source"]):
        table2.rows[0].cells[i].text = h
    for a in data.get("action_item_list", []):
        row = table2.add_row().cells
        row[0].text = str(a.get("item", ""))
        row[1].text = str(a.get("owner", ""))
        row[2].text = str(a.get("status", ""))
        row[3].text = str(a.get("source", ""))

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()