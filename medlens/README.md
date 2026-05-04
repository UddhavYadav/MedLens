# medlens — Main Application

This is the core MedLens application — a FastAPI backend that handles doctor auth, patient document uploads, knowledge base management, and clinical chat powered by MedGemma via Modal.

---

## Files

| File                     | Purpose                                       |
| ------------------------ | --------------------------------------------- |
| `main.py`                | FastAPI app — all routes and background tasks |
| `auth.py`                | Doctor registration and login                 |
| `db.py`                  | PostgreSQL connection and table creation      |
| `document_processing.py` | Parses PDF, DOCX, TXT, images, DICOM          |
| `document_repository.py` | Saves and checks document hashes in DB        |
| `dicom_processor.py`     | DICOM windowing (CXR/CT) and normalization    |
| `kb_manager.py`          | ChromaDB vector store and RAG retrieval       |
| `med_service.py`         | Modal remote function for MedGemma inference  |

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create `.env` file

```env
db_pass=YOUR_POSTGRES_PASSWORD
```

### 3. Make sure PostgreSQL is running

```bash
# Default config in db.py:
# host: localhost
# database: postgres
# user: postgres
# port: 5432
```

### 4. Make sure the Docling service is running

```bash
# From docling-service/
uvicorn docling_service:app --port 8001
```

### 5. Set up Modal

```bash
pip install modal
modal token new
modal deploy med_service.py
```

### 6. Run the app

```bash
uvicorn main:app --port 8000 --reload
```

---

## Database Tables

**`doctors`** — stores registered doctors

```
id, username, password_hash, created_at
```

**`patient_documents`** — stores uploaded document metadata

```
id, patient_id, file_name, file_hash, file_path, file_size, uploaded_at
```

---

## Runtime Directories

These are created automatically on startup and are excluded from git:

| Directory         | Purpose                    |
| ----------------- | -------------------------- |
| `uploads/`        | General upload storage     |
| `temp_uploads/`   | Per-task temporary files   |
| `knowledge_base/` | Per-patient document files |
| `chroma_db/`      | ChromaDB vector embeddings |

---

## Requirements

```
fastapi
uvicorn
psycopg2-binary
python-dotenv
pdfplumber
pdf2image
pydicom
numpy
pillow
python-magic
httpx
langchain-huggingface
langchain-chroma
langchain-core
modal
pydantic
```
