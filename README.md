# screenwiper_ai_v2

FastAPI를 사용하여 구현된 OCR(Optical Character Recognition) API입니다. Google Cloud Vision API를 활용하여 이미지에서 텍스트를 추출합니다.

## Features

-   Image analysis via URL (/analyze_images)
-   Image analysis via local file upload (/analyze_images_local) (Local Test 용도)
-

## Installation

1. Install required packages

```
pip install -r requirements.txt
```

2. Google Cloud

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
curl -X POST "http://localhost:8000/analyze_images" -H "Content-Type: application/json" -d "{\"imageUrls\": [\"https://example.com/image1.jpg\", \"https://example.com/image2.jpg\"]}"
```

2. Image Analysis via Local File Upload

**Request** :

```
curl -X POST "http://localhost:8000/analyze_images_local" -H "Content-Type: multipart/form-data" -F "files=@C:\screenWiperV2\test\test1.png" -F "files=@C:\screenWiperV2\test\test2.png"
```

## Response Format (수정예정)

```
{
  "data": [
    {
      "imageUrl": "https://example.com/image1.jpg",
      "extractedText": "Extracted text content"
    },
    {
      "imageUrl": "https://example.com/image2.jpg",
      "extractedText": "Extracted text content"
    }
  ]
}
```
