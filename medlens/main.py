from unittest import result
from fastapi import FastAPI, File, UploadFile, Form,BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import os
import shutil
from document_processing import Document_Processor
from kb_manager import add_to_kb
from med_service import appp,generate
import uuid
import modal
import time
import sys
import hashlib
import logging
from document_repository import hash_exists
from db import create_tables
from kb_manager import retrieve_context
from auth import register_doctor, login_doctor



logging.basicConfig(
    filename="app.log",
    level=logging.DEBUG
)





os.environ["PYTHONIOENCODING"] = "utf-8"  
results = {}  
chat_history=[]  
upload=False  
patient_task={}  
HASH_FILE = "hashes.txt"

app = FastAPI(title="Clinical Assistant API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
UPLOAD_DIR = "uploads"
KB_DIR = "knowledge_base"
STATIC_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(KB_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Storage
patient_sessions = {}
patient_knowledge = {}

class ChatRequest(BaseModel):
    patient_id: str
    message: str

create_tables()

# Serve frontend at root
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main HTML page"""
    html_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r",encoding="utf-8") as f:
            html_content = f.read()
        # Update fetch URLs to use relative paths
        html_content = html_content.replace(
            'http://127.0.0.1:8000/',
            '/'
        )
        return HTMLResponse(content=html_content)
    else:
        return HTMLResponse(
            content="<h1>Welcome to Clinical Assistant API</h1>"
                   "<p>Place your index.html in the 'static' folder</p>"
        )

# API endpoints (same as before)
@app.post("/chat/")
async def chat(request: ChatRequest,background_tasks: BackgroundTasks):
    patient_id = request.patient_id
    message = request.message
    task_id = str(uuid.uuid4())
    global upload
    if patient_id not in patient_sessions:
        patient_sessions[patient_id] = []


    patient_sessions[patient_id].append({
        "role": "user",
        "content": [{"type":"text","text":message}]
    })
    
    if upload:
        while patient_task[patient_id] not in results:
            time.sleep(1)
        up_msg=results[patient_task[patient_id]]

        new_content=add_prompt(message,up_msg["content"])

        llm_message=get_message(patient_id,new_content)


    
    
    

    if upload:
        background_tasks.add_task(process_clinical_response, task_id, patient_id, llm_message,upload)
    else:
        background_tasks.add_task(process_clinical_response, task_id, patient_id, patient_sessions[patient_id])
    
    upload=False


    
    return {"task_id": task_id}

def process_clinical_response(task_id: str, patient_id: str, llm_message: str,upload=False):
    reply = generate_clinical_response(patient_id, llm_message,upload)
    patient_sessions[patient_id].append({
        "role": "assistant",
        "content":[{"type":"text","text":reply}]
    })
    results[task_id] = {"status":"complete","reply": reply}



# Your background function - takes file PATHS not file objects
def process_files(task_id: str, file_paths: list, patient_id: str):
    contents = []
    names = []
    j=0
    
    for file_path in file_paths:
        if j>4:
            break
        names.append(os.path.basename(file_path))
        document_processor = Document_Processor(file_path)  # Pass path instead
        content = document_processor.handle_uploaded_file()
        contents.extend(content)
        j+=1
    
    # with appp.run():
    #     reply = generate.remote(msg_list[0])
    
    # Save result
    results[task_id] = {"status":"complete","content":contents , "files": names}
    print("done generatingg.")


@app.post("/upload/")
async def upload_files(
    background_tasks: BackgroundTasks,
    patient_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    if not files:
        return {"status": "⚠️ No files uploaded"}
    
    task_id = str(uuid.uuid4())
    global upload
    upload=True # mark upload here 
    
    # Save files to disk FIRST
    file_paths = []
    temp_dir = f"temp_uploads/{task_id}"
    os.makedirs(temp_dir, exist_ok=True)
    
    for file in files:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_paths.append(file_path)
    
    # Now add background task with file paths
    background_tasks.add_task(process_files, task_id, file_paths, patient_id)

    patient_task[patient_id]=task_id

    
    return {
        "status": f"✅ Processing started for patient {patient_id}",
        "task_id": task_id
    }

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    if task_id in results:
        return results[task_id]
    return {"status": "still processing"}


@app.post("/add_to_kb/")
async def add_to_knowledge_base(
    background_tasks: BackgroundTasks,
    patient_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    if not files:
        return {"status": "⚠️ No files to process"}
    
    kb_patient_dir = os.path.join(KB_DIR, patient_id)
    os.makedirs(kb_patient_dir, exist_ok=True)
    
    processed_files = []
    file_paths_and_hash = []

    for file in files:
        file_bytes = await file.read()

        if not file_bytes:
            continue

        file_hash = hashlib.sha256(file_bytes).hexdigest()

        if hash_exists_in_file(patient_id,file_hash):
            continue

        file_path = os.path.join(kb_patient_dir, file.filename)
        file_size = len(file_bytes)
        
        # ✅ FIXED
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)

        file_paths_and_hash.append({
            "path": file_path,
            "hash": file_hash,
            "file_name":file.filename,
            "file_size":len(file_bytes)
        })

        processed_files.append(file.filename)

    if file_paths_and_hash:
        extracted_info = add_to_kb(file_paths_and_hash, patient_id)

        if patient_id not in patient_knowledge:
            patient_knowledge[patient_id] = []

        patient_knowledge[patient_id].append({
            "files": processed_files,
            "content": extracted_info
        })

    return {
        "status": f"🧠 Added {len(processed_files)} file(s) to {patient_id}'s knowledge base",
        "files": processed_files
    }




@app.get("/patient/{patient_id}/history")
async def get_patient_history(patient_id: str):
    if patient_id not in patient_sessions:
        return {"history": []}
    return {"history": patient_sessions[patient_id]}

@app.get("/patient/{patient_id}/knowledge")
async def get_patient_knowledge(patient_id: str):
    if patient_id not in patient_knowledge:
        return {"knowledge": []}
    return {"knowledge": patient_knowledge[patient_id]}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "patients_active": len(patient_sessions),
        "kb_entries": sum(len(v) for v in patient_knowledge.values())
    }



def generate_clinical_response(patient_id: str, message,upload) -> str:
    print("The value of upload: ",upload)
    user_query = message[-1]["content"][0]["text"]
    context = retrieve_context(user_query, patient_id)  

    rag_prompt = f"""
You are a clinical assistant.

Use the following patient data to answer the question.

Patient Context:
{context}

Answer clinically and precisely.
"""

    system_role={"role":"system","content":[{"type":"text","text":rag_prompt}]}
   
    if message[0]["role"] == "system":
        message[0]=system_role
    else:
        message.insert(0, system_role)
    messages={"messages":message,"upload":upload}
    user_query = message[-1]["content"][0]["text"]
    print("The user query: ",message[0])
    print("zero index message complete here")
    print("The user query: ",message[1])
    with modal.enable_output():
        with appp.run():
            result=generate.remote(messages)
        result
    return result


def process_prompt():
    pass

def add_prompt(prompt,content):

    new_content=content.append({"type":"text","text":prompt})
    return content

def get_message(patient_id,new_content):

    new_message= patient_sessions[patient_id][:-1]+[{"role":"user","content":new_content}] 

    return new_message



def process_document(file_path: str) -> str:
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext == '.pdf':
        return "PDF document processed (implement PDF parsing)"
    elif file_ext in ['.png', '.jpg', '.jpeg']:
        return "Image processed (implement OCR/analysis)"
    else:
        return "Document processed"




def hash_exists_in_file(patient_id,file_hash: str) -> bool:
    return hash_exists(patient_id,file_hash)


def save_hash_to_file(file_hash: str):
    with open(HASH_FILE, "a") as f:
        f.write(file_hash + "\n")









class AuthRequest(BaseModel):
    username: str
    password: str

@app.post("/register/")
async def register(req: AuthRequest):
    success = register_doctor(req.username, req.password)
    if success:
        return {"status": "ok"}
    return {"status": "error", "message": "Username already exists"}

@app.post("/login/")
async def login(req: AuthRequest):
    if login_doctor(req.username, req.password):
        return {"status": "ok"}
    return {"status": "error", "message": "Invalid credentials"}
# use this to remove all gather files and folders of upload
