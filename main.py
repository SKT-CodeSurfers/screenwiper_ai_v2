import os
import io
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from google.cloud import vision
import requests
from PIL import Image
from typing import List
from datetime import datetime
from google.cloud import language_v1
import re
import httpx

# & FastAPI 인스턴스 생성
app = FastAPI()

# & Google Vision API 인증 파일 설정
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'json/screenwiper-919c75b2918f.json'

# & Vision API 클라이언트 설정
client_options = {'api_endpoint': 'eu-vision.googleapis.com'}
client = vision.ImageAnnotatorClient(client_options=client_options)

# & Natural Language API 클라이언트 설정 
nlp_client = language_v1.LanguageServiceClient()

# & Image Download
class ImageUrls(BaseModel):
    imageUrls: List[str]

async def download_image_from_url(image_url: str) -> Image.Image:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        return img.convert('RGB')
    except httpx.RequestError as e:
        raise HTTPException(status_code=400, detail=f"이미지 다운로드 중 오류가 발생했습니다: {e}")

# & perfom OCR
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

    return response.text_annotations[0].description if response.text_annotations else ""

# & perfom analyze Text
def analyze_entities(text:str):
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
    response = nlp_client.analyze_entities(document=document)
    return response.entities

def extract_information(entities,extracted_text):
    addresses = []
    other_entities = []
    store_name = None
    events = extract_dates_and_events(entities, extracted_text)


    for entity in entities:
        if entity.type_ == language_v1.Entity.Type.ADDRESS:
            addresses.append(entity.name)
        elif entity.type_ == language_v1.Entity.Type.ORGANIZATION:
            # ! 가게 이름으로 사용할 수 있는 첫 번째 조직명을  ORGANIZATION 저장
            if not store_name:
                store_name = entity.name
        else:
            other_entities.append(entity.name)


    return addresses, other_entities, store_name ,events

# & 카테고리2 (event)
def extract_dates_and_events(entities, text):
    events = []
    lines = text.split('\n')
    
    for entity in entities:
        if entity.type_ == language_v1.Entity.Type.DATE:
            date = entity.name
            normalized_date = parse_date(date)
            if normalized_date:
                for line in lines:
                    if date in line:
                        # Extract event name from the current line excluding the date
                        event_name = line.replace(date, "").strip()
                        events.append({
                            "name": event_name,
                            "date": normalized_date
                        })
    
    return events

def parse_date(date_str):
    formats = ['%Y-%m-%d', '%d/%m/%Y', '%d.%m.%Y', '%y-%m-%d', '%Y년 %m월 %d일', '%Y%m%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return date_str # 파싱에 실패하면 원래 문자열 반환

# & 카테고리1 (시간)
def extract_operating_hours(text):
    # 영업 시간 정규식 패턴
    OPERATING_HOURS_PATTERN = (
        r'(?:오전|오후|매일|매일|월요일|화요일|수요일|목요일|금요일|토요일|일요일|월|화|수|목|금|토|일|평일|주말)?\s*(\d{1,2}):(\d{2})\s*(?:~|-\s*)\s*(?:오전|오후|매일|월요일|화요일|수요일|목요일|금요일|토요일|일요일|월|화|수|목|금|토|일|평일|주말)?\s*(\d{1,2}):(\d{2})|'  # 오전/오후 형식
        r'(\d{1,2}):(\d{2})\s*(?:~|-\s*)\s*(\d{1,2}):(\d{2})|'  # 24시간 형식
        r'(매일|월요일|화요일|수요일|목요일|금요일|토요일|일요일)\s*(\d{1,2}):(\d{2})\s*(?:~|-\s*)\s*(\d{1,2}):(\d{2})'
    )
    
    matches = re.findall(OPERATING_HOURS_PATTERN, text)
    operating_hours = []

    for match in matches:
        # 매칭된 그룹을 확인하여 빈 문자열을 제외한 부분만 처리
        match = [m for m in match if m]
        
        if len(match) == 4:
            # 24시간 형식
            start_time = f"{match[0]}:{match[1]}"
            end_time = f"{match[2]}:{match[3]}"
            operating_hours.append(f"{start_time} - {end_time}")
        
        elif len(match) == 8:
            # 오전/오후 형식
            start_period = match[0] if match[0] else ""
            end_period = match[4] if match[4] else ""
            start_time = f"{start_period} {match[1]}:{match[2]}" if start_period else f"{match[1]}:{match[2]}"
            end_time = f"{end_period} {match[3]}:{match[4]}" if end_period else f"{match[3]}:{match[4]}"
            operating_hours.append(f"{start_time} - {end_time}")
        
        elif len(match) == 10:
            # 요일 형식
            day = match[0]
            start_time = f"{match[1]}:{match[2]}"
            end_time = f"{match[3]}:{match[4]}"
            operating_hours.append(f"{day} {start_time} - {end_time}")
    
    return operating_hours



def generate_response(category_id, addresses, other_entities, store_name,extracted_text,events):
    if category_id == 1:  # ! 장소 정보

        operating_hours = extract_operating_hours(extracted_text)

        return {
            "categoryId": 1,
            "title": store_name if store_name else (addresses[0] if addresses else "Unknown Place"), # ! 수정 필요 
            "address": addresses[0] if addresses else "",
            "operatingHours": operating_hours,
            "summary": ", ".join(other_entities[:3]),
        }
    elif category_id == 2:  # ! 일정 정보
        return {
            "categoryId": 2,
            "title": other_entities[0] if other_entities else "Unknown Event",
            "list": events,
        }
    else:  # ! 기타
        return {
            "categoryId": 3,
            "title": other_entities[0] if other_entities else "Miscellaneous",
            "summary": ", ".join(other_entities),
        }


@app.post("/analyze_images")
async def analyze_images(image_urls: ImageUrls):
    results = []
    for image_url in image_urls.imageUrls:
        try:
            image_content  = await download_image_from_url(image_url)

            extracted_text = perform_ocr(image_content)
            entities = analyze_entities(extracted_text)

            addresses, other_entities, store_name ,events = extract_information(entities,extracted_text)

            # ! 카테고리 설정하기 
            if addresses:
                category_id = 1
            elif events:
                category_id = 2
            else:
                category_id = 3

            response_data = generate_response(category_id, addresses, other_entities, store_name, extracted_text,events)
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
            image_content = Image.open(io.BytesIO(contents))
            
            # OCR 결과 처리
            extracted_text = perform_ocr(image_content)
            entities = analyze_entities(extracted_text)
            
            addresses, other_entities, store_name ,events = extract_information(entities,extracted_text)

            # ! 카테고리 설정하기 
            if addresses:
                category_id = 1
            elif events:
                category_id = 2
            else:
                category_id = 3

            response_data = generate_response(category_id, addresses, other_entities, store_name, extracted_text,events)
            results.append(response_data)
        
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})

    return JSONResponse(content={"data": results})

# ! **** 



#  & return response


@app.get("/")
async def root():
    return {"message": "Welcome to the OCR API"}


if __name__ == "__main__":
    app.run(debug=True)