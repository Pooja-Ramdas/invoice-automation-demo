import os
import re
import csv
import json
import shutil
import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

APP_DIR = Path(__file__).resolve().parent
INBOX_DIR = APP_DIR / "inbox"
ARCHIVE_DIR = APP_DIR / "archive"
REVIEW_DIR = APP_DIR / "manual_review"
LOG_PATH = APP_DIR / "invoice_log.csv"
for folder in (INBOX_DIR, ARCHIVE_DIR, REVIEW_DIR):
    folder.mkdir(exist_ok=True)

FIELDS = ["timestamp", "fileName", "invoiceNo", "vendor", "date", "amount", "gst",
          "status", "reason", "submitterEmail"]

st.set_page_config(page_title="Invoice Automation", page_icon="🧾", layout="wide")
st.title("🧾 Invoice Processing Automation")
st.caption("Upload invoice PDFs, extract fields, validate, detect duplicates, log results, and archive files.")

def read_log():
    if not LOG_PATH.exists():
        return []
    try:
        with LOG_PATH.open("r", newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def write_log(row):
    exists = LOG_PATH.exists()
    with LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if not exists or LOG_PATH.stat().st_size == 0:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in FIELDS})

def extract_text(pdf_path):
    try:
        reader = PdfReader(str(pdf_path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as e:
        return ""

def first_match(patterns, text, flags=re.IGNORECASE | re.MULTILINE):
    for pattern in patterns:
        m = re.search(pattern, text, flags)
        if m:
            return m.group(1).strip()
    return ""

def extract_invoice_fields(text):
    # These patterns handle common text-based invoice layouts. Scanned PDFs need OCR.
    invoice_no = first_match([
        r"(?:invoice\s*(?:number|no\.?|#|id))\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-\/]+)",
        r"\b(INV[-/ ]?\d{3,})\b",
    ], text)
    vendor = first_match([
        r"(?:vendor|supplier|seller|company\s*name)\s*[:\-]\s*([^\n\r]+)",
    ], text)
    date = first_match([
        r"(?:invoice\s*date|date)\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})",
        r"(?:invoice\s*date|date)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    ], text)
    amount_raw = first_match([
        r"(?:total\s*(?:amount|due|payable)?|grand\s*total|invoice\s*total)\s*[:\-]?\s*(?:₹|INR|Rs\.?)?\s*([0-9,]+(?:\.\d{1,2})?)",
    ], text)
    gst_raw = first_match([
        r"(?:GST(?:\s*amount)?|tax\s*amount|total\s*tax)\s*[:\-]?\s*(?:₹|INR|Rs\.?)?\s*([0-9,]+(?:\.\d{1,2})?)",
    ], text)
    def num(value):
        try:
            return float(value.replace(",", "")) if value else None
        except ValueError:
            return None
    return {
        "invoiceNo": invoice_no,
        "vendor": vendor,
        "date": date,
        "amount": num(amount_raw),
        "gst": num(gst_raw),
    }

def send_email(to_address, row):
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", user)
    if not (host and user and password and sender and to_address):
        return False, "Email not configured; result is shown in the app and saved to CSV."
    msg = EmailMessage()
    msg["Subject"] = f"Invoice {row['invoiceNo'] or row['fileName']}: {row['status']}"
    msg["From"] = sender
    msg["To"] = to_address
    msg.set_content(
        f"Invoice processing result\n\nFile: {row['fileName']}\n"
        f"Invoice number: {row['invoiceNo']}\nVendor: {row['vendor']}\n"
        f"Date: {row['date']}\nAmount: {row['amount']}\nGST: {row['gst']}\n"
        f"Status: {row['status']}\nReason: {row['reason']}\n"
    )
    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        return True, f"Email sent to {to_address}."
    except Exception as e:
        return False, f"Email failed: {e}"

def process_pdf(uploaded_file, submitter_email):
    safe_name = Path(uploaded_file.name).name
    inbox_path = INBOX_DIR / safe_name
    with inbox_path.open("wb") as f:
        f.write(uploaded_file.getbuffer())
    text = extract_text(inbox_path)
    fields = extract_invoice_fields(text)
    amount_missing = fields["amount"] is None
    required_missing = [name for name in ("invoiceNo", "vendor", "date", "amount", "gst")
                        if fields.get(name) in ("", None)]
    previous = read_log()
    is_duplicate = any(
        (r.get("invoiceNo", "").strip().casefold() == str(fields["invoiceNo"]).strip().casefold())
        and (r.get("vendor", "").strip().casefold() == str(fields["vendor"]).strip().casefold())
        and r.get("status") == "Accepted"
        and fields["invoiceNo"] and fields["vendor"]
        for r in previous
    )
    if not text.strip():
        status, reason = "Manual Review", "No readable text found; scanned PDF may need OCR."
    elif required_missing:
        status, reason = "Manual Review", "Missing or unreadable field(s): " + ", ".join(required_missing)
    elif is_duplicate:
        status, reason = "Duplicate", "Invoice number and vendor match a previously accepted invoice."
    else:
        status, reason = "Accepted", "All required fields were extracted and validated."
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fileName": safe_name,
        **fields,
        "status": status,
        "reason": reason,
        "submitterEmail": submitter_email.strip(),
    }
    write_log(row)
    target_dir = ARCHIVE_DIR if status == "Accepted" else REVIEW_DIR
    target_path = target_dir / safe_name
    # Avoid overwriting a file with the same name.
    if target_path.exists():
        target_path = target_dir / f"{target_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{target_path.suffix}"
    shutil.copy2(inbox_path, target_path)
    email_ok, email_message = send_email(submitter_email.strip(), row)
    row["_emailMessage"] = email_message
    row["_emailOK"] = email_ok
    return row

with st.sidebar:
    st.header("Settings")
    submitter_email = st.text_input("Email for result notification", placeholder="you@example.com")
    st.info("Email sends only when SMTP settings are configured. Otherwise results are still logged locally.")
    st.caption("CSV log: invoice_log.csv")
    st.caption("Accepted PDFs: archive/")
    st.caption("Duplicate / review PDFs: manual_review/")

uploaded = st.file_uploader("Upload one or more invoice PDFs", type=["pdf"], accept_multiple_files=True)
if uploaded and st.button("Process invoices", type="primary"):
    results = []
    progress = st.progress(0)
    for i, file in enumerate(uploaded):
        try:
            results.append(process_pdf(file, submitter_email))
        except Exception as e:
            st.error(f"Could not process {file.name}: {e}")
        progress.progress((i + 1) / len(uploaded))
    st.session_state["last_results"] = results

results = st.session_state.get("last_results", [])
if results:
    st.subheader("Latest processing results")
    display_rows = [{k: r.get(k, "") for k in FIELDS} for r in results]
    st.dataframe(display_rows, use_container_width=True, hide_index=True)
    for r in results:
        if r.get("_emailMessage"):
            st.caption(f"{r['fileName']}: {r['_emailMessage']}")
    csv_bytes = (LOG_PATH.read_bytes() if LOG_PATH.exists() else b"")
    if csv_bytes:
        st.download_button("Download complete CSV log", data=csv_bytes, file_name="invoice_log.csv", mime="text/csv")

st.subheader("Processing history")
history = read_log()
if history:
    st.dataframe(history[::-1], use_container_width=True, hide_index=True)
    if LOG_PATH.exists():
        st.download_button("Download CSV history", data=LOG_PATH.read_bytes(),
                           file_name="invoice_log.csv", mime="text/csv", key="history_download")
else:
    st.write("No invoices processed yet.")

with st.expander("Demo notes"):
    st.markdown(
        "- Works with **text-based PDFs**. Scanned/image-only PDFs need OCR.\n"
        "- Field extraction uses common labels such as Invoice No, Vendor, Date, Total Amount, and GST.\n"
        "- Duplicate detection compares invoice number + vendor against previously accepted rows in the CSV.\n"
        "- This is a local demo app. It does not call your UiPath API workflow unless you separately connect a deployed endpoint."
    )
