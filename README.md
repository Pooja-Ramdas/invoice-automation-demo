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
   
## Testing checklist
- Upload a text-based invoice with all fields → `Accepted`.
- Upload an invoice with missing/unclear amount or GST → `Manual Review`.
- Upload the same accepted invoice again → `Duplicate`.
- Check CSV and folders.
- PDF extraction will not work reliably on scanned PDFs without OCR.
- 
# invoice-automation-demo
Invoice processing automation demo using Streamlit and UiPath
