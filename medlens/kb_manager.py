from document_processing import Document_Processor
import os 
from med_service import appp,generate
import modal
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import uuid
import re
from document_repository import save_document

DB_NAME="./chroma_db"

system_prompt2="""
You are a clinical document processing system.
you will be provided with the image and text content extracted from docling with image place holder ignore them
Your task is to summarize the provided medical document content in precise meaning full way in medical terms the content should be medium to short but not too short max 150 words it will be used for RAG
dont' repeat lines in last 
"""

def add_to_kb(file_paths_and_hash,patient_id):
    # file_paths=[i["path"] for i in file_paths_and_hash]
    summaries=get_summary(file_paths_and_hash,patient_id)
    vectorstore(summaries,patient_id)
    print(summaries)

def get_summary(file_paths_and_hash,patient_id):
    summaries=[]
    for path in file_paths_and_hash:
        processor=Document_Processor(path["path"])
        content = processor.handle_uploaded_file()
        summary=chat(content)
        summaries.append({
            "file_name": os.path.basename(path["path"]),
            "summary": summary,
            "hash":path["hash"]
        })
        save_document(patient_id,path['file_name'],path['hash'],path['path'],path['file_size'])

    return summaries

def chat(user_content):
    message=[{"role":"system","content":[{"type":"text","text":system_prompt2}]},{"role":"user","content":user_content}]
    summary=modal_call(message)
    return summary

def modal_call(message,upload=True):
    messages={"messages":message,"upload":upload,"mode":"summary"}
    with modal.enable_output():
        with appp.run():
            result=generate.remote(messages)
        result
    return result

def vectorstore(summaries,patient_id):
    print("inside vectorstore")
    documents = [
    Document(
        page_content=summary["summary"],
        metadata={"patient_id": patient_id,"file_name":summary["file_name"],"hash":summary["hash"]}   
    )
    for i, summary in enumerate(summaries)
    ]
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    if os.path.exists(DB_NAME):
        vectorstore = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings,
        collection_name=f"patient_{patient_id}"
        )

        vectorstore.add_documents(documents)
    else:
        vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory="./chroma_db",
        collection_name=f"patient_{patient_id}"
        )





def make_safe_collection_name(patient_id: str) -> str:
    patient_id = patient_id.strip()  # remove spaces/newlines
    
    # remove invalid characters
    patient_id = re.sub(r'[^a-zA-Z0-9._-]', '', patient_id)

    name = f"patient_{patient_id}"

    # remove invalid start/end characters
    name = name.strip("._-")

    if len(name) < 3:
        raise ValueError("Collection name too short after sanitization")

    return name
    

def retrieve_context(query, patient_id, k=3):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vectorstore = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings,
        collection_name=f"patient_{patient_id}"
    )

    results = vectorstore.similarity_search(query, k=k)

    context = "\n\n".join([doc.page_content for doc in results])

    return context