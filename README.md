# MedLens — AI-Powered Clinical Assistant

MedLens is a medical document intelligence platform that lets doctors upload patient documents, build a per-patient knowledge base, and query it using a medically fine-tuned LLM through a simple chat interface.

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Doctor (Browser)                   │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│            MedLens API  (localhost:8000)             │
│                    medlens/                          │
│                                                      │
│  Upload → Process → Summarize → Embed → Chat         │
└──────────┬──────────────────────┬───────────────────┘
           │                      │
           ▼                      ▼
┌──────────────────┐   ┌─────────────────────────────┐
│  Docling Service │   │     Modal (Remote GPU)       │
│  localhost:8001  │   │  google/medgemma-1.5-4b-it   │
│ docling-service/ │   │       med_service.py         │
└──────────────────┘   └─────────────────────────────┘
           │
           ▼
┌──────────────────┐
│   PostgreSQL     │
│   ChromaDB       │
└──────────────────┘
```

---

## Repository Structure

```
MedLens/
├── README.md                        ← you are here
├── .gitignore
│
├── medlens/                         ← main application
│   ├── main.py                      # FastAPI backend
│   ├── auth.py                      # Doctor auth
│   ├── db.py                        # PostgreSQL connection
│   ├── document_processing.py       # Multi-format document processor
│   ├── document_repository.py       # DB operations
│   ├── dicom_processor.py           # DICOM → PNG conversion
│   ├── kb_manager.py                # Vector store + RAG
│   ├── med_service.py               # Modal GPU inference
│   ├── static/                      # Frontend (index.html)
│   ├── requirements.txt
│   └── README.md
│
└── docling-service/                 ← document parsing microservice
    ├── docling_service.py           # FastAPI microservice
    ├── requirements.txt
    └── README.md
```

---

## Tech Stack

| Layer            | Technology                            |
| ---------------- | ------------------------------------- |
| API              | FastAPI                               |
| Database         | PostgreSQL                            |
| Vector Store     | ChromaDB                              |
| Embeddings       | `all-MiniLM-L6-v2` (HuggingFace)      |
| LLM              | `google/medgemma-1.5-4b-it` via Modal |
| Document Parsing | Docling, pdfplumber, pdf2image        |
| Medical Imaging  | pydicom, Pillow                       |
| GPU Compute      | Modal (T4)                            |

---

## Supported File Types

| Format                    | How it's processed                       |
| ------------------------- | ---------------------------------------- |
| `.pdf`                    | Docling (Markdown) + pdfplumber (images) |
| `.docx`                   | Docling (Markdown) + embedded images     |
| `.txt`                    | Plain text                               |
| `.jpg` / `.jpeg` / `.png` | Direct image bytes                       |
| `.dcm`                    | DICOM windowing (CXR / CT) → PNG         |

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/MedLens.git
cd MedLens
```

### 2. Start the Docling service

```bash
cd docling-service
pip install -r requirements.txt
uvicorn docling_service:app --port 8001
```

### 3. Start the main app

```bash
cd medlens
pip install -r requirements.txt
# create your .env file (see medlens/README.md)
uvicorn main:app --port 8000 --reload
```

### 4. Deploy Modal function

```bash
cd medlens
modal deploy med_service.py
```

Visit `http://localhost:8000` to open the UI.

---

## How RAG Works

1. Doctor uploads patient documents
2. Documents are parsed into text + images
3. MedGemma generates a clinical summary per document (max 150 words)
4. Summaries are embedded and stored in ChromaDB under the patient's collection
5. On each chat query, top-k relevant summaries are retrieved and injected into the system prompt
6. MedGemma answers clinically based on the retrieved context

---

## API Endpoints

| Method | Endpoint                  | Description                         |
| ------ | ------------------------- | ----------------------------------- |
| `POST` | `/register/`              | Register a doctor                   |
| `POST` | `/login/`                 | Doctor login                        |
| `POST` | `/upload/`                | Upload files for a patient session  |
| `POST` | `/add_to_kb/`             | Add files to patient knowledge base |
| `POST` | `/chat/`                  | Chat with clinical assistant        |
| `GET`  | `/result/{task_id}`       | Poll background task result         |
| `GET`  | `/patient/{id}/history`   | Get chat history                    |
| `GET`  | `/patient/{id}/knowledge` | Get KB entries                      |
| `GET`  | `/health`                 | Health check                        |

---

## Security Notes

- Passwords are hashed with SHA-256 — consider upgrading to `bcrypt` for production
- No JWT auth yet — planned for future release
- Never commit your `.env` file

---

## License

MIT
