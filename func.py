import io
import json
import base64
import logging
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR
from fdk import response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    ocr = PaddleOCR(use_angle_cls=True, lang="japan", use_gpu=False, det_db_box_thresh=0.5)
except Exception as e:
    logger.error(f"PaddleOCR initialization failed: {str(e)}")
    ocr = None

def extract_text_from_pdf(pdf_bytes):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text("text")
        doc.close()
        return text.strip() if text.strip() else "No text extracted"
    except Exception as e:
        logger.error(f"Text extraction error: {str(e)}")
        return f"Text extraction error: {str(e)}"

def ocr_pdf_page(pdf_bytes):
    if ocr is None:
        return "OCR unavailable: initialization failed"
    
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        ocr_results = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            img_np = np.array(img)
            
            result = ocr.ocr(img_np, cls=True)
            page_results = []
            if result and len(result) > 0:
                for line in result[0]:
                    coords = line[0]
                    text = line[1][0]
                    confidence = line[1][1]
                    page_results.append({
                        "coords": coords,
                        "text": text,
                        "confidence": confidence
                    })
            
            ocr_results.append({
                "page": page_num + 1,
                "results": page_results
            })
        
        doc.close()
        return ocr_results
    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        return f"OCR error: {str(e)}"

def handle(ctx, data: io.BytesIO = None):
    try:
        body = json.loads(data.getvalue())
        pdf_base64 = body["pdf_base64"]
        
        if not pdf_base64:
            return response.Response(
                ctx,
                status_code=400,
                response_data=json.dumps({"error": "Missing pdf_base64 in input data"})
            )
        
        try:
            pdf_bytes = base64.b64decode(pdf_base64)
        except base64.binascii.Error:
            return response.Response(
                ctx,
                status_code=400,
                response_data=json.dumps({"error": "Invalid Base64 string"})
            )
        
        extracted_text = extract_text_from_pdf(pdf_bytes)
        ocr_results = ocr_pdf_page(pdf_bytes)
        
        return response.Response(
            ctx,
            status_code=200,
            response_data=json.dumps({
                "status": "success",
                "extracted_text": extracted_text,
                "ocr_results": ocr_results
            })
        )
    except Exception as e:
        logger.error(f"Function error: {str(e)}")
        return response.Response(
            ctx,
            status_code=500,
            response_data=json.dumps({"error": f"Function error: {str(e)}"})
        )