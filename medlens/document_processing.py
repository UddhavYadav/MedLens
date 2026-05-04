import pdfplumber
from pdf2image import convert_from_path
# from transformers import pipeline
from PIL import Image
# import torch
import magic 
import tempfile
import shutil
import os
import io
import PIL
from dicom_processor import dicom_to_bytes
import httpx
import zipfile
import logging 



class Document_Processor:
    def __init__(self, file):
        self.file = file
        pass



    def handle_uploaded_file(self):
        # mime= self.detect_file_type()
        try:
            if self.file.lower().endswith(".pdf"):
                return self.process_pdfs(self.file)

            elif self.file.lower().endswith(".txt"):
                return self.txt_processor()


            elif self.file.lower().endswith(".docx"):
                return self.docx_processor(self.file)

            elif self.file.lower().endswith((".jpg", ".jpeg", ".png")):
                return self.image_processor()

            elif self.file.lower().endswith(".dcm"):
                return self.dcm_processor()
        except:
            logging.exception(f"Error processing file: {self.file}")
            raise 
        

        else:
            raise ValueError("Unsupported file type")



    def pil_to_bytes(self,img: "PIL.Image.Image") -> bytes:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def img_path_to_bytes(self,path)->bytes:
        img = Image.open(path)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()



    def process_pdfs(self,PDF_PATH):
        print("Converting PDF pages to images...")
        page_images = convert_from_path(
            PDF_PATH,
            dpi=200,            # good balance for medical images
            fmt="png"
        )
        abs_path = os.path.abspath(PDF_PATH)
        print("Absolute path:", abs_path)

        content = []

        with pdfplumber.open(PDF_PATH) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):

                print(f"Processing page {page_num}...")

                # Extract text
                text = page.extract_text() or ""

                # Detect images
                has_images = len(page.images) > 0

                # -------------------------
                # Case 1: Page has images
                # -------------------------
                if has_images:
                    page_image = page_images[page_num - 1]  # PIL Image
                    image_bytes = self.pil_to_bytes(page_image) 

                    content.extend([
                            {
                                "type": "image",
                                "image": image_bytes
                            }
                        ]
                    )

               
        content.append(
                {
                    "type": "text",
                    "text": f"""
                    Below is the extracted text from whole pdf 
                    {self.pdf_docling()}
                    """
                }
            )



        return content

    def get_message(self):
        content=self.handle_uploaded_file()
        message={"role":"user","content":content}
        msg={"messages":message}
        return msg

    def txt_processor(self):
        with open(self.file, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        content = [
            {
                "type": "text",
                "text": text
            }
        ]

        return content


    def docx_processor(self,path):
        text=self.docx_docling()
        images=self.extract_images_as_bytes()
        suffix="This is the text of word file below are the images of the same word file"
        content=[{"type":"text","text":suffix+text}]
        for img_bytes in images:
            content.append({"type":"image","image":img_bytes})
        return content

    def image_processor(self):
        content=[]
        img_bytes=self.img_path_to_bytes(self.file)
        content.append({"type":"image","image":img_bytes})
        return content

    def dcm_processor(self):
        content=[]
        img_bytes=dicom_to_bytes(self.file)
        content.append({"type":"image","image":img_bytes})
        return content

    def pdf_docling(self):
        docling_response = self.call_docling_service()
        markdown = docling_response["markdown"]
        return markdown

    def docx_docling(self):
        docling_response = self.call_docling_service()
        markdown = docling_response["markdown"]
        return markdown

    def call_docling_service(self):
        abs_path = os.path.abspath(self.file)
        print("Absolute path:", abs_path)
        with httpx.Client(timeout=300.0) as client:  # 5 min timeout
            response = client.post(
                "http://localhost:8001/convert/",
                json={"file_path": abs_path}
            )
            return response.json()

    def extract_images_as_bytes(self):
        images = []

        with zipfile.ZipFile(self.file, 'r') as docx:
            for file in docx.namelist():
                if file.startswith("word/media/"):
                    image_bytes = docx.read(file)
                    images.append(image_bytes)

        return images


