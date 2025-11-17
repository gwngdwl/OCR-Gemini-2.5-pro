import os
import ssl
import warnings
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyPDF2 import PdfReader, PdfWriter

# חייב להיות לפני כל ייבוא של google-genai או httpx
os.environ["SSL_CERT_FILE"] = r"C:\ProgramData\NetFree\CA\netfree-ca-bundle-curl.crt"
os.environ["REQUESTS_CA_BUNDLE"] = r"C:\ProgramData\NetFree\CA\netfree-ca-bundle-curl.crt"
os.environ["CURL_CA_BUNDLE"] = r"C:\ProgramData\NetFree\CA\netfree-ca-bundle-curl.crt"

# עקיפת בדיקת SSL (זמני - בגלל NetFree)
ssl._create_default_https_context = ssl._create_unverified_context

# Monkey patch ל-httpx לפני ייבוא google.genai
import httpx
_original_httpx_client_init = httpx.Client.__init__

def _patched_httpx_client_init(self, *args, **kwargs):
    kwargs['verify'] = False
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    _original_httpx_client_init(self, *args, **kwargs)

httpx.Client.__init__ = _patched_httpx_client_init

from google import genai
from google.genai import types

# הגדרות
API_KEY = "AIzaSyC1Z4hueDxJMglrj1B4XjGrP4c4rd2HeMg"
SOURCE_PDF = r"C:\Users\lenovo\Downloads\test\Hebrewbooks_org_16210.pdf"
OUTPUT_TXT = r"C:\Users\lenovo\Downloads\test\output_full.txt"
PAGES_PER_CHUNK = 5

print("קורא את הקובץ...")
reader = PdfReader(SOURCE_PDF)
total_pages = len(reader.pages)
print(f"הקובץ מכיל {total_pages} עמודים")
print(f"יעבד ב-chunks של {PAGES_PER_CHUNK} עמודים\n")

print("מתחבר ל-Gemini...")
client = genai.Client(api_key=API_KEY)

# הכנת כל ה-chunks מראש
total_chunks = (total_pages + PAGES_PER_CHUNK - 1) // PAGES_PER_CHUNK
chunks_info = []

print("מכין chunks...")
for start_page in range(0, total_pages, PAGES_PER_CHUNK):
    end_page = min(start_page + PAGES_PER_CHUNK, total_pages)
    chunk_num = (start_page // PAGES_PER_CHUNK) + 1
    
    # יצירת PDF זמני עם החלק הנוכחי
    writer = PdfWriter()
    for i in range(start_page, end_page):
        writer.add_page(reader.pages[i])
    
    temp_pdf = f"temp_chunk_{start_page + 1}_{end_page}.pdf"
    with open(temp_pdf, "wb") as f:
        writer.write(f)
    
    chunks_info.append({
        'chunk_num': chunk_num,
        'start_page': start_page + 1,
        'end_page': end_page,
        'temp_pdf': temp_pdf
    })

print(f"נוצרו {len(chunks_info)} chunks\n")

def process_chunk(chunk_info):
    """מעבד chunk בודד"""
    chunk_num = chunk_info['chunk_num']
    start_page = chunk_info['start_page']
    end_page = chunk_info['end_page']
    temp_pdf = chunk_info['temp_pdf']
    
    print(f"[Chunk {chunk_num}/{total_chunks}] מעלה עמודים {start_page}-{end_page}...")
    
    with open(temp_pdf, "rb") as f:
        pdf_bytes = f.read()
    
    file_obj = io.BytesIO(pdf_bytes)
    uploaded = client.files.upload(
        file=file_obj,
        config=types.UploadFileConfig(mime_type="application/pdf")
    )
    
    print(f"[Chunk {chunk_num}/{total_chunks}] שולח לעיבוד...")
    
    prompt = """לפניך מסמך PDF. 
כתוב לי את תוכן המסמך במדוייק, אל תוסיף כלום מדעתך.

חשוב:
- אל תכלול כותרות עליונות (headers)
- אל תכלול הערות שוליים (footnotes)
- רק את תוכן הטקסט הראשי של המסמך
- הקובץ הוא שני טורים! קרא את הטור הימני ולאחר מכן את הטור השמאלי"""
    
    contents = [
        types.Part.from_uri(file_uri=uploaded.uri, mime_type="application/pdf"),
        types.Part.from_text(text=prompt)
    ]
    
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=None,
            response_mime_type='text/plain',
            temperature=0.8
        )
    )
    
    chunk_text = response.text.strip() if response.text else ""
    print(f"[Chunk {chunk_num}/{total_chunks}] הושלם! התקבלו {len(chunk_text)} תווים")
    
    return {
        'chunk_num': chunk_num,
        'text': chunk_text
    }

# עיבוד מקביל - 2 בקשות במקביל (בגלל מגבלת 2 RPM)
print("מתחיל עיבוד מקביל (2 chunks במקביל)...\n")
results = {}

with ThreadPoolExecutor(max_workers=2) as executor:
    # שליחת כל ה-chunks
    future_to_chunk = {executor.submit(process_chunk, chunk): chunk for chunk in chunks_info}
    
    # איסוף תוצאות כשהן מסתיימות
    for future in as_completed(future_to_chunk):
        try:
            result = future.result()
            results[result['chunk_num']] = result['text']
            
            # שמירה חלקית (backup) - לפי סדר
            all_text = [results[i] for i in sorted(results.keys())]
            with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
                f.write("\n\n".join(all_text))
            
            print(f"נשמרו {len(results)}/{total_chunks} chunks עד כה\n")
            
        except Exception as e:
            chunk = future_to_chunk[future]
            print(f"שגיאה ב-chunk {chunk['chunk_num']}: {e}\n")

# סידור סופי לפי מספר chunk
all_text = [results[i] for i in sorted(results.keys())]
with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    f.write("\n\n".join(all_text))

print(f"\n{'='*60}")
print("הושלם!")
print(f"{'='*60}")
print(f"סה\"כ עובדו {total_pages} עמודים")
print(f"סה\"כ {len(all_text)} chunks")
print(f"הטקסט המלא נשמר ב-{OUTPUT_TXT}")
