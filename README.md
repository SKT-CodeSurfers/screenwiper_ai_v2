# screenwiper_ai_v2

FastAPI를 사용하여 구현된 OCR(광학 문자 인식) 및 NLP(자연어 처리) API입니다. Google Cloud Vision API를 사용하여 이미지에서 텍스트를 추출하고, Google Cloud Natural Language API를 사용하여 텍스트 분석 및 분류를 수행합니다.

## Features

-   Image analysis via URL (`/analyze_images`)
-   Image analysis via local file upload (`/analyze_images_local`) (**For local testing**)
-   Text categorization into three categories (`def analyze_entities`):
    1. Place information (restaurants, stores, etc.)
    2. Schedule information
    3. Other miscellaneous information

## Installation

1. Install required packages

```
pip install -r requirements.txt
```

2. Set up Google Cloud

-   Google Cloud 프로젝트를 생성하고 Vision API를 활성화
-   서비스 계정 키를 생성하고 `json/screenwiper-919c75b2918f.json` 경로에 저장

## Running the Application

```
uvicorn main:app --reload
```

server will run at http://localhost:8000

## API Usage

1. Image Analysis via URL

**Request** :

```
curl -X POST "http://localhost:8000/analyze_images" \
-H "Content-Type: application/json" \
-d '{
  "imageUrls": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ]
}'

```

2. Image Analysis via Local File Upload

**Request** :

```
curl -X POST "http://localhost:8000/analyze_images_local" \
-H "Content-Type: multipart/form-data" \
-F "files=@C:\screenWiperV2\test\test1.png" \
-F "files=@C:\screenWiperV2\test\test2.png"

```

## Response Format

### Category 1: Place Information

```
{
  "categoryId": 1,
  "title": "Store Name",
  "address": "Store Address",
  "operatingHours": "Operating Hours",
  "summary": "Brief summary of the place"
}
```

### Category 2: Schedule Information

```
{
  "categoryId": 2,
  "title": "Schedule Information",
  "list": [
    {
      "name": "Event Name",
      "date": "Event Date"
    },
    // ... more events
  ]
}
```

### Category 3: Other Information

```
{
  "categoryId": 3,
  "title": "Other Information",
  "summary": "Summary of the extracted text"
}
```
