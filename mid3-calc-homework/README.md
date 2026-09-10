# 중3 계산교정 7일 Streamlit 앱

- 하루 18문제 × 7일 = 126문제
- 분수 / 부호 혼합 / 번분수 / 제곱근 / 분모 유리화 / 혼합 / 종합
- 자동채점
- 90% 미만 오답 재도전
- 관리자 결과표 + CSV 다운로드
- 모바일 브라우저 지원

## Streamlit Community Cloud 배포
Entry point: `mid3-calc-homework/streamlit_app.py`

같은 폴더의 `requirements.txt`가 자동으로 사용됩니다.

### 관리자 PIN
Streamlit Cloud의 Advanced settings > Secrets에 아래처럼 입력하면 됩니다.

```toml
admin_pin = "원하는PIN"
```

Secrets를 설정하지 않으면 임시 기본값은 `2580`입니다. 공개 저장소이므로 실제 운영 전에는 반드시 Secrets로 PIN을 바꾸는 것을 권장합니다.

## 저장 관련 주의
현재 제출기록은 SQLite 로컬 파일에 저장됩니다. Streamlit Community Cloud의 로컬 파일은 영구 저장소로 간주하면 안 됩니다. 7일 훈련 중에는 관리자 화면의 CSV 다운로드로 백업할 수 있습니다. 영구 저장/푸시 알림은 다음 단계에서 Supabase 또는 Google Sheets API 같은 외부 저장소를 연결하는 방식이 적절합니다.
