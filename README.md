# PDF to Text with Gemini AI

מערכת לעיבוד קבצי PDF והמרתם לטקסט באמצעות Gemini AI.

## שימוש ב-GitHub Actions

### הגדרה ראשונית

1. עבור ל-Settings → Secrets and variables → Actions
2. הוסף Secret חדש בשם `GEMINI_API_KEY` עם מפתח ה-API שלך

### הרצת עיבוד

1. עבור ל-Actions → Process PDF with Gemini
2. לחץ על "Run workflow"
3. הזן:
   - **קישור ישיר לקובץ PDF** - URL של הקובץ (חייב להיות נגיש)
   - **כמה עמודים בכל chunk** - ברירת מחדל: 5
4. לחץ "Run workflow"

### הורדת התוצאה

לאחר שהעיבוד מסתיים:
1. לחץ על ה-workflow run שהסתיים
2. גלול למטה ל-Artifacts
3. הורד את `processed-text`

## שימוש מקומי

### דרישות

```bash
pip install google-genai PyPDF2 httpx
```

### הרצה

```bash
cd test
python process_full_pdf.py
```

ערוך את הקובץ כדי לשנות:
- `SOURCE_PDF` - נתיב לקובץ PDF
- `OUTPUT_TXT` - נתיב לקובץ פלט
- `PAGES_PER_CHUNK` - כמה עמודים בכל chunk
- `API_KEY` - מפתח Gemini API

## סקריפטים נוספים

### test_k2pdfopt.py
בדיקת חיתוך עמוד בודד עם k2pdfopt:
```bash
python test_k2pdfopt.py 2  # עמוד 2
```

### test_gemini.py
בדיקת Gemini על עמוד בודד:
```bash
python test_gemini.py
```

### test_gemini_multi.py
בדיקת Gemini על מספר עמודים:
```bash
python test_gemini_multi.py 5  # 5 עמודים
```

## מגבלות Gemini 2.5 Pro

- **בקשות לדקה (RPM):** 2
- **טוקנים לדקה (TPM):** 125,000
- **בקשות ביום (RPD):** 50

הסקריפט משתמש ב-2 threads במקביל כדי למקסם את השימוש במגבלת ה-RPM.

## תכונות

- ✅ עיבוד מקביל (2 chunks במקביל)
- ✅ שמירה אוטומטית של התקדמות
- ✅ תמיכה ב-SSL של NetFree
- ✅ זיהוי אוטומטי של טורים (ימין לשמאל)
- ✅ סינון כותרות עליונות והערות שוליים
