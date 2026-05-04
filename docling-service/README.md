# docling-service — Document Parsing Microservice

A lightweight FastAPI microservice that converts PDF and DOCX files into Markdown using [Docling](https://github.com/DS4SD/docling). It runs independently and is called by the main MedLens app at `http://localhost:8001`.

---

## Files

| File                 | Purpose                               |
| -------------------- | ------------------------------------- |
| `docling_service.py` | FastAPI app with `/convert/` endpoint |
| `requirements.txt`   | Dependencies                          |

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the service

```bash
uvicorn docling_service:app --port 8001
```

---

## API

### `POST /convert/`

Converts a PDF or DOCX file at the given path to Markdown.

**Request body:**

```json
{
  "file_path": "/absolute/path/to/file.pdf"
}
```

**Response:**

```json
{
  "markdown": "# Document Title\n\nExtracted content...",
  "status": "success"
}
```

> **Note:** The file must be accessible on the same machine where this service is running. The main MedLens app sends the absolute file path after saving the upload to disk.

---

## Docling Pipeline Config

| Option          | Value                        |
| --------------- | ---------------------------- |
| OCR             | Disabled                     |
| Table structure | Enabled (with cell matching) |
| Picture images  | Enabled (scale 2x)           |
| DOCX pipeline   | SimplePipeline               |

---

## Requirements

```
fastapi
uvicorn
docling
```
