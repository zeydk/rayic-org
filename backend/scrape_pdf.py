import requests
import pdfplumber

url = "https://depremzemin.ibb.istanbul/wp-content/uploads/2020/12/Maltepe.pdf"
pdf_path = "/Users/zeyd/.gemini/antigravity/scratch/rayic-org/backend/data/Maltepe.pdf"

print("Downloading...")
res = requests.get(url, verify=False)
with open(pdf_path, 'wb') as f:
    f.write(res.content)

print("Extracting tables...")
with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        if tables:
            for t in tables:
                # Check if this table has neighborhood level data
                text = str(t)
                if "Zemin" in text or "Vs30" in text or "PGA" in text or "Mahalle" in text:
                    print(f"--- Page {i+1} Table ---")
                    for row in t[:5]:  # print first 5 rows
                        print(row)
