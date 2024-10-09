import os
import io
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from google.cloud import vision
import requests
from PIL import Image
from typing import List

# & FastAPI 인스턴스 생성
app = FastAPI()

# & Google Vision API 인증 파일 설정
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'json/screenwiper-919c75b2918f.json'

# & Vision API 클라이언트 설정
client_options = {'api_endpoint': 'eu-vision.googleapis.com'}
client = vision.ImageAnnotatorClient(client_options=client_options)


# & Image Download
class ImageUrls(BaseModel):
    imageUrls: List[str]

def download_image_from_url(image_url: str) -> Image.Image:
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        return img.convert('RGB')
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"이미지 다운로드 중 오류가 발생했습니다: {e}")


# & perfom OC
def perform_ocr(image: Image.Image):
    # 이미지를 바이트로 변환
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    image_content = img_byte_arr.getvalue()

    image = vision.Image(content=image_content)

    # & 텍스트 검출 요청 
    response = client.text_detection(image=image)

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

    return response.text_annotations


@app.post("/analyze_images")
async def analyze_images(image_urls: ImageUrls):
    results = []
    for image_url in image_urls.imageUrls:
        try:
            image = download_image_from_url(image_url)
            ocr_result = perform_ocr(image)

            # OCR 결과 처리
            extracted_text = ocr_result[0].description if ocr_result else ""


            response_data = {
                "imageUrl": image_url,
                "extractedText": extracted_text,
            }
            results.append(response_data)
        except Exception as e:
            results.append({"imageUrl": image_url, "error": str(e)})

    return JSONResponse(content={"data": results})



# ! local test용  ****
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from typing import List


@app.post("/analyze_images_local")
async def analyze_images(files: List[UploadFile] = File(...)):
    results = []

    for file in files:
        try:
            contents = await file.read()
            img = Image.open(io.BytesIO(contents))
            
            ocr_result = perform_ocr(img)
            # OCR 결과 처리
            extracted_text = ocr_result[0].description if ocr_result else ""

            response_data = {
                "extractedText": extracted_text,
            }
            results.append(response_data)
        
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})

    return JSONResponse(content={"data": results})

# ! **** 

@app.get("/")
async def root():
    return {"message": "Welcome to the OCR API"}


if __name__ == "__main__":
    app.run(debug=True)