from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import streamlit as st
from PIL import Image, ImageOps


st.set_page_config(
    page_title="WEBP → 1000×1000 JPG 변환기",
    page_icon="🖼️",
    layout="wide",
)

st.title("WEBP → 1000×1000 JPG 자동 변환기")
st.caption("WEBP 이미지를 업로드하면 네이버 스마트스토어 대표이미지에 맞는 1000×1000 JPG로 자동 변환합니다.")


def safe_filename(name: str, suffix: str = "_1000x1000") -> str:
    stem = Path(name).stem.strip() or "converted_image"
    blocked = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for char in blocked:
        stem = stem.replace(char, "_")
    return f"{stem}{suffix}.jpg"


def open_uploaded_image(uploaded_file) -> Image.Image | None:
    try:
        image = Image.open(BytesIO(uploaded_file.getvalue()))
        image = ImageOps.exif_transpose(image)
        return image.convert("RGB")
    except Exception:
        return None


def fit_contain_1000(image: Image.Image, bg_color: tuple[int, int, int]) -> Image.Image:
    """원본 전체가 잘리지 않게 1000×1000 안에 넣고, 남는 영역은 배경색으로 채웁니다."""
    canvas_size = 1000
    src = image.convert("RGB")
    ratio = min(canvas_size / src.width, canvas_size / src.height)
    new_w = max(1, int(src.width * ratio))
    new_h = max(1, int(src.height * ratio))
    resized = src.resize((new_w, new_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (canvas_size, canvas_size), bg_color)
    x = (canvas_size - new_w) // 2
    y = (canvas_size - new_h) // 2
    canvas.paste(resized, (x, y))
    return canvas


def fit_cover_1000(image: Image.Image) -> Image.Image:
    """1000×1000을 꽉 채우도록 확대한 뒤 중앙 기준으로 자릅니다."""
    canvas_size = 1000
    src = image.convert("RGB")
    ratio = max(canvas_size / src.width, canvas_size / src.height)
    new_w = max(1, int(src.width * ratio))
    new_h = max(1, int(src.height * ratio))
    resized = src.resize((new_w, new_h), Image.Resampling.LANCZOS)

    left = max(0, (new_w - canvas_size) // 2)
    top = max(0, (new_h - canvas_size) // 2)
    return resized.crop((left, top, left + canvas_size, top + canvas_size))


def edge_extend_1000(image: Image.Image, bg_color: tuple[int, int, int]) -> Image.Image:
    """
    원본 전체를 보존하면서 1000×1000에 넣고, 남는 좌우/상하 영역은 이미지 가장자리 픽셀을 늘려 채웁니다.
    마네킹컷이나 제품컷처럼 흰 여백이 많은 사진에 유용합니다.
    """
    canvas_size = 1000
    src = image.convert("RGB")
    ratio = min(canvas_size / src.width, canvas_size / src.height)
    new_w = max(1, int(src.width * ratio))
    new_h = max(1, int(src.height * ratio))
    fitted = src.resize((new_w, new_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (canvas_size, canvas_size), bg_color)
    x = (canvas_size - new_w) // 2
    y = (canvas_size - new_h) // 2
    canvas.paste(fitted, (x, y))

    if new_w < canvas_size:
        left_margin = max(0, x)
        right_margin = max(0, canvas_size - (x + new_w))

        if left_margin > 0:
            left_strip = fitted.crop((0, 0, 1, new_h)).resize((left_margin, new_h), Image.Resampling.BILINEAR)
            canvas.paste(left_strip, (0, y))

        if right_margin > 0:
            right_strip = fitted.crop((new_w - 1, 0, new_w, new_h)).resize((right_margin, new_h), Image.Resampling.BILINEAR)
            canvas.paste(right_strip, (x + new_w, y))

    if new_h < canvas_size:
        top_margin = max(0, y)
        bottom_margin = max(0, canvas_size - (y + new_h))

        if top_margin > 0:
            top_strip = canvas.crop((0, y, canvas_size, y + 1)).resize((canvas_size, top_margin), Image.Resampling.BILINEAR)
            canvas.paste(top_strip, (0, 0))

        if bottom_margin > 0:
            bottom_strip = canvas.crop((0, y + new_h - 1, canvas_size, y + new_h)).resize(
                (canvas_size, bottom_margin),
                Image.Resampling.BILINEAR,
            )
            canvas.paste(bottom_strip, (0, y + new_h))

    return canvas


def image_to_jpg_bytes(image: Image.Image, quality: int) -> bytes:
    buffer = BytesIO()
    image.save(
        buffer,
        format="JPEG",
        quality=int(quality),
        optimize=True,
        progressive=True,
        subsampling=0,
    )
    return buffer.getvalue()


with st.sidebar:
    st.header("변환 설정")

    mode = st.radio(
        "1000×1000 변환 방식",
        [
            "전체 보존",
            "꽉 채우기",
            "가장자리 확장",
        ],
        index=0,
        help=(
            "전체 보존: 사진이 잘리지 않음 / "
            "꽉 채우기: 여백 없이 채우지만 일부가 잘릴 수 있음 / "
            "가장자리 확장: 원본 전체를 살리면서 남는 공간을 사진 가장자리로 채움"
        ),
    )

    bg_choice = st.selectbox(
        "배경색",
        ["흰색", "아이보리", "연회색", "검정"],
        index=0,
    )

    bg_map = {
        "흰색": (255, 255, 255),
        "아이보리": (250, 247, 239),
        "연회색": (245, 245, 245),
        "검정": (0, 0, 0),
    }
    bg_color = bg_map[bg_choice]

    quality = st.slider("JPG 품질", 85, 98, 96, step=1)
    st.caption("품질을 높이면 선명하지만 파일 용량이 커집니다. 기본값 96을 권장합니다.")

uploaded_files = st.file_uploader(
    "WEBP 파일 업로드",
    type=["webp"],
    accept_multiple_files=True,
    help="여러 장을 한 번에 업로드할 수 있습니다.",
)

if not uploaded_files:
    st.info("변환할 .webp 이미지를 업로드해 주세요.")
    st.stop()

st.success(f"{len(uploaded_files)}장 업로드됨")

zip_buffer = BytesIO()
converted_count = 0

cols = st.columns(2)

with ZipFile(zip_buffer, "w") as zipf:
    for index, uploaded in enumerate(uploaded_files):
        source_image = open_uploaded_image(uploaded)

        with cols[index % 2]:
            with st.container(border=True):
                st.markdown(f"### 이미지 {index + 1}")
                st.caption(uploaded.name)

                if source_image is None:
                    st.error("이미지를 읽지 못했습니다.")
                    continue

                st.write(f"원본 크기: **{source_image.width} × {source_image.height}px**")

                if mode == "꽉 채우기":
                    result_image = fit_cover_1000(source_image)
                elif mode == "가장자리 확장":
                    result_image = edge_extend_1000(source_image, bg_color)
                else:
                    result_image = fit_contain_1000(source_image, bg_color)

                jpg_bytes = image_to_jpg_bytes(result_image, quality)
                out_name = safe_filename(uploaded.name)

                st.image(jpg_bytes, caption="변환 결과 1000×1000 JPG", use_container_width=True)
                st.download_button(
                    "이 JPG 다운로드",
                    data=jpg_bytes,
                    file_name=out_name,
                    mime="image/jpeg",
                    use_container_width=True,
                    key=f"download_{index}",
                )

                zipf.writestr(out_name, jpg_bytes)
                converted_count += 1

if converted_count:
    st.divider()
    st.download_button(
        "전체 JPG ZIP 다운로드",
        data=zip_buffer.getvalue(),
        file_name="webp_to_jpg_1000x1000.zip",
        mime="application/zip",
        type="primary",
        use_container_width=True,
    )
    st.caption(f"총 {converted_count}장의 JPG를 ZIP으로 받을 수 있습니다.")
