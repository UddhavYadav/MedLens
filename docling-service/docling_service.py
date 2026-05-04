from fastapi import FastAPI
from pydantic import BaseModel
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.document_converter import DocumentConverter, PdfFormatOption,WordFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions

app = FastAPI()

# Setup converter once at startup
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.generate_picture_images = True
pipeline_options.images_scale = 2
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options = TableStructureOptions(do_cell_matching=True)

converter = DocumentConverter(format_options={
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
    InputFormat.DOCX: WordFormatOption(pipeline_cls=SimplePipeline) 
})

class ConvertRequest(BaseModel):
    file_path: str

@app.post("/convert/")
def convert_pdf(request: ConvertRequest):
    # Convert the file at given path
    result = converter.convert(request.file_path)
    markdown = result.document.export_to_markdown()
    
    return {"markdown": markdown, "status": "success"}

# Run: uvicorn docling_service:app --port 8001