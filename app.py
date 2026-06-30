from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import streamlit as st
from PIL import Image, ImageOps


st.set_page_config(
    page_title="이미지 → 1000×1000 JPG 테두리정리 변환기",
    page_icon="🖼️",
    layout="wide",
)

st.title("이미지 → 1000×1000 JPG 테두리정리 변환기")
st.caption(
    "WEBP, PNG, JPG, JPEG, BMP, TIF, TIFF, GIF 이미지를 업로드하면 "
    "바깥 여백을 정리한 뒤, 옷 전체를 최대한 보존하면서 1000×1000 JPG로 변환합니다. "
    "남는 정사각형 영역은 사진 가장자리 픽셀을 늘려 채웁니다."
)

SUPPORTED_TYPES = ["webp", "png", "jpg", "jpeg", "bmp", "tif", "tiff", "gif"]


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
        if getattr(image, "is_animated", False):
            try:
                image.seek(0)
            except Exception:
                pass

        if image.mode in ("RGBA", "LA"):
            bg = Image.new("RGBA", image.size, (255, 255, 255, 255))
            image = Image.alpha_composite(bg, image.convert("RGBA")).convert("RGB")
        elif image.mode == "P":
            image = image.convert("RGBA")
            bg = Image.new("RGBA", image.size, (255, 255, 255, 255))
            image = Image.alpha_composite(bg, image).convert("RGB")
        else:
            image = image.convert("RGB")
        return image
    except Exception:
        return None


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


def trim_edges(image: Image.Image, trim_percent: float) -> Image.Image:
    src = image.convert("RGB")
    if trim_percent <= 0:
        return src

    w, h = src.size
    trim_x = int(w * (trim_percent / 100.0) / 2)
    trim_y = int(h * (trim_percent / 100.0) / 2)

    left = min(max(0, trim_x), max(0, w - 2))
    top = min(max(0, trim_y), max(0, h - 2))
    right = max(left + 1, w - trim_x)
    bottom = max(top + 1, h - trim_y)

    return src.crop((left, top, right, bottom))


def fit_contain_1000(image: Image.Image, bg_color: tuple[int, int, int]) -> Image.Image:
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
    return canvas


def fit_cover_1000(image: Image.Image) -> Image.Image:
    canvas_size = 1000
    src = image.convert("RGB")
    ratio = max(canvas_size / src.width, canvas_size / src.height)
    new_w = max(1, int(src.width * ratio))
    new_h = max(1, int(src.height * ratio))
    fitted = src.resize((new_w, new_h), Image.Resampling.LANCZOS)

    left = max(0, (new_w - canvas_size) // 2)
    top = max(0, (new_h - canvas_size) // 2)
    return fitted.crop((left, top, left + canvas_size, top + canvas_size))


def edge_extend_1000(image: Image.Image, bg_color: tuple[int, int, int]) -> Image.Image:
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


def trim_then_edge_extend_1000(
    image: Image.Image,
    trim_percent: float,
    bg_color: tuple[int, int, int],
) -> Image.Image:
    trimmed = trim_edges(image, trim_percent)
    return edge_extend_1000(trimmed, bg_color)


def convert_image(
    image: Image.Image,
    mode: str,
    trim_percent: float,
    bg_color: tuple[int, int, int],
) -> Image.Image:
    if mode == "테두리 정리 + 가장자리 확장":
        return trim_then_edge_extend_1000(image, trim_percent, bg_color)
    if mode == "가장자리 확장만":
        return edge_extend_1000(image, bg_color)
    if mode == "전체 보존":
        return fit_contain_1000(image, bg_color)
    if mode == "테두리 정리 + 전체 보존":
        return fit_contain_1000(trim_edges(image, trim_percent), bg_color)
    if mode == "꽉 채우기":
        return fit_cover_1000(trim_edges(image, trim_percent))
    return trim_then_edge_extend_1000(image, trim_percent, bg_color)


with st.sidebar:
    st.header("변환 설정")

    mode = st.radio(
        "1000×1000 변환 방식",
        [
            "테두리 정리 + 가장자리 확장",
            "가장자리 확장만",
            "전체 보존",
            "테두리 정리 + 전체 보존",
            "꽉 채우기",
        ],
        index=0,
        help=(
            "기본값은 이전 대표이미지 마네킹컷 방식과 같은 '테두리 정리 + 가장자리 확장'입니다. "
            "옷 전체를 보존하면서 바깥 여백만 줄이고, 남는 정사각형 영역은 사진 가장자리로 채웁니다."
        ),
    )

    trim_percent = st.slider(
        "테두리 정리",
        0.0,
        20.0,
        4.0,
        step=0.5,
        help=(
            "사진 바깥쪽 여백을 조금 잘라 상품을 더 크게 보이게 합니다. "
            "옷이 잘리면 값을 낮추고, 여백이 너무 많으면 값을 올리세요."
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

    st.caption("추천값: 테두리 정리 3~6%. 옷이 잘리면 0~2%로 낮추세요.")

uploaded_files = st.file_uploader(
    "이미지 파일 업로드",
    type=SUPPORTED_TYPES,
    accept_multiple_files=True,
    help="WEBP, PNG, JPG, JPEG, BMP, TIF, TIFF, GIF 파일을 여러 장 한 번에 업로드할 수 있습니다.",
)

if not uploaded_files:
    st.info("변환할 이미지 파일을 업로드해 주세요.")
    st.stop()

st.success(f"{len(uploaded_files)}장 업로드됨")

st.caption("지원 확장자: " + ", ".join(ext.upper() for ext in SUPPORTED_TYPES))

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

                result_image = convert_image(
                    source_image,
                    mode=mode,
                    trim_percent=float(trim_percent),
                    bg_color=bg_color,
                )

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
        file_name="image_to_jpg_1000x1000.zip",
        mime="application/zip",
        type="primary",
        use_container_width=True,
    )
    st.caption(f"총 {converted_count}장의 JPG를 ZIP으로 받을 수 있습니다.")
