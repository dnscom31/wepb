# 이미지 → 1000×1000 JPG 테두리정리 변환기

기존의 WEBP 전용 변환기를 확장해서, 여러 이미지 확장자를 한 번에 업로드하고 1000×1000 JPG로 변환하는 Streamlit 앱입니다.

## 지원 확장자

- WEBP
- PNG
- JPG
- JPEG
- BMP
- TIF
- TIFF
- GIF

## 이번 수정 핵심

기존:
- `.webp` 파일만 업로드 가능

수정 후:
- `webp, png, jpg, jpeg, bmp, tif, tiff, gif` 업로드 가능

또한 다음 처리도 포함했습니다.

- PNG/GIF 같은 투명 배경 이미지는 흰 배경 기준으로 JPG 변환
- 애니메이션 GIF는 첫 프레임 기준으로 변환
- 결과 파일은 모두 `1000×1000 JPG`

## 기본 변환 방식

기본값은 `테두리 정리 + 가장자리 확장`입니다.

1. 사진 바깥 테두리/여백을 먼저 조금 잘라냅니다.
2. 옷 전체는 최대한 보존하면서 1000×1000 안에 맞춥니다.
3. 남는 좌우/상하 공간은 사진 가장자리 픽셀을 늘려 채웁니다.

## 변환 방식

### 테두리 정리 + 가장자리 확장
### 가장자리 확장만
### 전체 보존
### 테두리 정리 + 전체 보존
### 꽉 채우기

## 추천 설정

- 일반 의류 모델컷: 테두리 정리 3~5%
- 마네킹컷/제품컷: 테두리 정리 4~8%
- 옷이 잘리면: 테두리 정리 0~2%
- 여백이 너무 많으면: 테두리 정리 6~10%

## GitHub 파일 구성

```text
app.py
requirements.txt
packages.txt
README.md
.streamlit/config.toml
.gitignore
```

## Streamlit Cloud 설정

- Main file path: `app.py`

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```
