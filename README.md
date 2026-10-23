# Invoice Automation Demo (Windows, no UiPath Robot required)

## What this demo does
- Upload PDF invoices in a browser-based Streamlit page.
- Extract common invoice fields from text-based PDFs.
- Validate required fields and mark missing/unreadable fields `Manual Review`.
- Check invoice number + vendor against previously accepted invoices in `invoice_log.csv`.
- Mark matches as `Duplicate`.
- Save every result to CSV.
- Copy accepted PDFs to `archive/`; copy duplicates and review cases to `manual_review/`.
- Optionally email the result when SMTP environment variables are configured.

**Important:** this app is a local Python demo and does not automatically call the UiPath API Workflow you built. The UiPath workflow currently demonstrates the validation decision for supplied JSON input. Connecting the app to a deployed UiPath endpoint requires its endpoint URL and authentication details. Do not claim those two pieces are integrated until that connection is configured and tested.

## Run it on Windows
1. Install Python 3.11+ if it is not already installed. If you cannot install software, use a Python environment you already have or a hosted Python environment; local file archiving and SMTP configuration may differ in hosted environments.
2. Extract this ZIP to a folder, e.g. `C:\InvoiceBot`.
3. Open that folder in File Explorer.
4. Click the address bar, type `cmd`, press Enter.
5. Run:
   ```
   py -m pip install -r requirements.txt
   py -m streamlit run app.py
   ```
   If `py` is not recognized, try `python` instead.
6. A browser tab opens. Upload PDFs and click **Process invoices**.
7. The app creates `invoice_log.csv`, `inbox`, `archive`, and `manual_review` next to `app.py`.

## Email (optional)
Email is skipped unless all SMTP environment variables are configured:
- `SMTP_HOST` e.g. `smtp.gmail.com`
- `SMTP_PORT` e.g. `587`
- `SMTP_USER` sender email
- `SMTP_PASSWORD` an app password or SMTP credential (never paste it into the app source)
- `SMTP_FROM` optional; defaults to SMTP_USER

For Gmail, use an App Password if your account supports it; do not use your normal account password. You can demonstrate the workflow without email and clearly state that notification is optional/unconfigured.

## Testing checklist
- Upload a text-based invoice with all fields → `Accepted`.
- Upload an invoice with missing/unclear amount or GST → `Manual Review`.
- Upload the same accepted invoice again → `Duplicate`.
- Check CSV and folders.
- PDF extraction will not work reliably on scanned PDFs without OCR.

## Screen recording plan (2–3 minutes)
1. Before recording, open the app and prepare 3 PDFs: one complete invoice, one with amount omitted, and a copy of the accepted invoice for duplicate test. Ensure the PDFs contain selectable text.
2. Start Windows recording with `Win + Alt + R` (Xbox Game Bar). If that shortcut does not work, press `Win + G`, open Capture, then Record. Windows may not record some protected/administrator windows.
3. Record the browser app:
   - show title and upload a valid invoice;
   - click Process invoices and show Accepted;
   - upload the missing-amount PDF and show Manual Review;
   - upload the same valid PDF again and show Duplicate;
   - show Processing history and download CSV;
   - briefly show `archive` and `manual_review` folders in File Explorer.
4. If showing UiPath, record a separate short clip of the API Workflow Debug result returning `Accepted` for JSON test input. State honestly that the Streamlit demo and UiPath API workflow are separate until the API endpoint is connected.
5. Stop with `Win + Alt + R`. The clip is normally saved under `Videos\Captures`. Check it before submitting.

## Suggested narration
"I built an invoice processing demo. The Streamlit interface accepts PDF uploads. The app extracts invoice number, vendor, date, total amount and GST from readable PDF text, validates required fields, checks duplicates using the CSV history, records each result, and archives accepted files separately from manual-review cases. The UiPath API Workflow separately demonstrates the decision logic for a supplied JSON invoice payload. Connecting the Streamlit app to the deployed UiPath endpoint is the remaining integration step."
