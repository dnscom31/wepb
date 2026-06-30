from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import streamlit as st
from PIL import Image, ImageOps


st.set_page_config(
    page_title="WEBP → 1000×1000 JPG 스마트 변환기",
    page_icon="🖼️",
    layout="wide",
)

st.title("WEBP → 1000×1000 JPG 스마트 변환기")
st.caption(
    "WEBP 이미지를 업로드하면 네이버 스마트스토어 대표이미지에 맞는 1000×1000 JPG로 자동 변환합니다. "
    "기본값은 모델/상품이 크게 보이도록 자동 스마트 크롭을 적용합니다."
)


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


def sample_background_color(image: Image.Image) -> tuple[int, int, int]:
    rgb = image.convert("RGB")
    w, h = rgb.size
    points = [
        (0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
        (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2),
    ]
    colors = [rgb.getpixel((max(0, min(w - 1, x)), max(0, min(h - 1, y)))) for x, y in points]
    return tuple(int(sum(channel) / len(colors)) for channel in zip(*colors))


def detect_subject_bbox(image: Image.Image) -> tuple[float, float, float, float] | None:
    """
    배경과 색 차이가 있는 영역을 상품/모델 영역으로 추정합니다.
    흰 배경 상품컷, 모델컷, 마네킹컷에서 빠르게 동작하도록 단순한 방식으로 구성했습니다.
    """
    rgb = image.convert("RGB")
    src_w, src_h = rgb.size
    if src_w < 2 or src_h < 2:
        return None

    bg = sample_background_color(rgb)
    preview = rgb.copy()
    preview.thumbnail((420, 420), Image.Resampling.LANCZOS)
    px = preview.load()
    pw, ph = preview.size

    xs: list[int] = []
    ys: list[int] = []

    threshold = 28
    for y in range(ph):
        for x in range(pw):
            r, g, b = px[x, y]
            diff = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
            if diff > threshold * 3:
                xs.append(x)
                ys.append(y)

    if not xs or not ys:
        return None

    left_p, right_p = min(xs), max(xs)
    top_p, bottom_p = min(ys), max(ys)

    scale_x = src_w / pw
    scale_y = src_h / ph
    return (
        left_p * scale_x,
        top_p * scale_y,
        right_p * scale_x,
        bottom_p * scale_y,
    )


def crop_square(
    image: Image.Image,
    crop_side: float,
    center_x: float,
    center_y: float,
) -> Image.Image:
    src = image.convert("RGB")
    w, h = src.size

    crop_side = max(1.0, min(float(crop_side), float(w), float(h)))
    half = crop_side / 2

    left = center_x - half
    top = center_y - half

    left = max(0.0, min(float(w) - crop_side, left))
    top = max(0.0, min(float(h) - crop_side, top))

    right = left + crop_side
    bottom = top + crop_side

    cropped = src.crop((int(left), int(top), int(right), int(bottom)))
    return cropped.resize((1000, 1000), Image.Resampling.LANCZOS)


def fit_contain_1000(image: Image.Image, bg_color: tuple[int, int, int]) -> Image.Image:
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


def smart_model_crop_1000(image: Image.Image, zoom_strength: float = 1.0) -> Image.Image:
    """
    이전 대표이미지 생성기 방향:
    - 모델/상품 영역을 감지
    - 1000×1000 안에서 모델/상품이 크게 보이도록 정사각형 크롭
    - 너무 과하게 자르지 않도록 안전 여백 유지
    """
    src = image.convert("RGB")
    w, h = src.size
    bbox = detect_subject_bbox(src)

    if bbox is None:
        return fit_cover_1000(src)

    left, top, right, bottom = bbox
    bbox_w = max(1.0, right - left)
    bbox_h = max(1.0, bottom - top)

    side_base = min(w, h)

    # 상품/모델 주변 여백. 값이 작을수록 더 크게 보임.
    padding_factor = 1.12 - (zoom_strength - 1.0) * 0.10
    padding_factor = max(1.02, min(1.18, padding_factor))

    desired_side = max(bbox_w, bbox_h) * padding_factor

    # 너무 과하게 확대되어 얼굴/팔/밑단이 잘리지 않도록 제한
    min_side = side_base * 0.68
    max_side = side_base
    crop_side = max(min_side, min(max_side, desired_side))

    center_x = (left + right) / 2
    center_y = (top + bottom) / 2

    # 모델컷은 얼굴 쪽 여백이 부족하면 답답해 보이므로 살짝 위쪽 기준으로 보정
    center_y -= crop_side * 0.025

    return crop_square(src, crop_side, center_x, center_y)


def mannequin_preserve_1000(image: Image.Image, bg_color: tuple[int, int, int]) -> Image.Image:
    """
    마네킹컷/상품 전체컷용.
    전체가 잘리지 않게 보존하되, 정사각형 부족 영역은 가장자리 확장으로 채움.
    """
    return edge_extend_1000(image, bg_color)


def convert_image(
    image: Image.Image,
    mode: str,
    bg_color: tuple[int, int, int],
    zoom_strength: float,
) -> Image.Image:
    if mode == "자동 스마트 크롭":
        return smart_model_crop_1000(image, zoom_strength=zoom_strength)
    if mode == "모델컷 크게":
        return smart_model_crop_1000(image, zoom_strength=max(1.15, zoom_strength))
    if mode == "상품 전체 보존":
        return mannequin_preserve_1000(image, bg_color)
    if mode == "전체 보존":
        return fit_contain_1000(image, bg_color)
    if mode == "꽉 채우기":
        return fit_cover_1000(image)
    if mode == "가장자리 확장":
        return edge_extend_1000(image, bg_color)
    return smart_model_crop_1000(image, zoom_strength=zoom_strength)


with st.sidebar:
    st.header("변환 설정")

    mode = st.radio(
        "1000×1000 변환 방식",
        [
            "자동 스마트 크롭",
            "모델컷 크게",
            "상품 전체 보존",
            "전체 보존",
            "꽉 채우기",
            "가장자리 확장",
        ],
        index=0,
        help=(
            "자동 스마트 크롭: 이전 대표이미지 기능처럼 상품/모델이 크게 보이도록 자동 크롭 / "
            "모델컷 크게: 상반신·착용컷을 더 크게 / "
            "상품 전체 보존: 마네킹컷·제품컷 전체를 살림"
        ),
    )

    zoom_strength = st.slider(
        "자동 확대 강도",
        0.8,
        1.3,
        1.0,
        step=0.05,
        help="자동 스마트 크롭과 모델컷 크게 모드에서만 사용합니다. 높일수록 모델/상품이 더 크게 보입니다.",
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
    st.caption("기본값은 자동 스마트 크롭 + 품질 96입니다.")

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

                result_image = convert_image(
                    source_image,
                    mode=mode,
                    bg_color=bg_color,
                    zoom_strength=float(zoom_strength),
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
        file_name="webp_to_jpg_1000x1000.zip",
        mime="application/zip",
        type="primary",
        use_container_width=True,
    )
    st.caption(f"총 {converted_count}장의 JPG를 ZIP으로 받을 수 있습니다.")
