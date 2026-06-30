# WEBP → 1000×1000 JPG 자동 변환기

Streamlit에서 `.webp` 이미지를 업로드하면 1000×1000 JPG로 자동 변환하는 앱입니다.

## 주요 기능

- WEBP 여러 장 업로드
- 1000×1000 JPG 자동 변환
- 개별 JPG 다운로드
- 전체 ZIP 다운로드
- JPG 품질 조절
- 배경색 선택
- 변환 방식 3종 지원

## 변환 방식

### 1. 전체 보존

원본 이미지가 잘리지 않게 1000×1000 안에 넣고, 남는 영역은 선택한 배경색으로 채웁니다.

### 2. 꽉 채우기

1000×1000을 빈틈 없이 채우도록 확대 후 중앙 기준으로 자릅니다.  
일부 가장자리가 잘릴 수 있습니다.

### 3. 가장자리 확장

원본 전체를 보존하면서 1000×1000에 넣고, 남는 공간은 사진 가장자리 픽셀을 늘려 채웁니다.  
마네킹컷, 제품컷, 흰 배경 사진에 유용합니다.

## GitHub 파일 구성

```text
app.py
requirements.txt
packages.txt
README.md
.streamlit/config.toml
```

## Streamlit Cloud 설정

- Main file path: `app.py`
- Python 패키지: `requirements.txt`
- 리눅스 패키지: 별도 필수 없음

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```
