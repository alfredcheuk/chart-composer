import io
import json
import os
import re
import zipfile

import streamlit as st
from streamlit_paste_button import paste_image_button as pib
from PIL import Image, ImageChops, ImageDraw, ImageFont

# --- Config ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TITLES_PATH = os.path.join(SCRIPT_DIR, "chart_titles.json")
FONT_PATH = os.path.join(SCRIPT_DIR, "assets", "DINPro-Bold.otf")

BG_COLOR_DARK = (42, 46, 60, 255)
BG_COLOR_TRANSPARENT = (0, 0, 0, 0)
CORNER_RADIUS = 30
MARGIN = 80
TITLE_FONT_SIZE = 36
TITLE_COLOR = (255, 255, 255, 255)
GAP_TITLE_CHART = 40
TARGET_WIDTH = 1500


def load_titles():
    if os.path.exists(TITLES_PATH):
        with open(TITLES_PATH) as f:
            return json.load(f)
    return {}


def to_slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def round_corners(image, radius):
    corner_mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(corner_mask)
    draw.rounded_rectangle(
        [(0, 0), (image.size[0] - 1, image.size[1] - 1)],
        radius=radius,
        fill=255,
    )
    result = image.copy()
    existing_alpha = result.getchannel("A")
    combined_alpha = ImageChops.multiply(existing_alpha, corner_mask)
    result.putalpha(combined_alpha)
    return result


def scale_chart(chart, target_width):
    w, h = chart.size
    if w < target_width:
        ratio = target_width / w
        new_w = target_width
        new_h = int(h * ratio)
        return chart.resize((new_w, new_h), Image.LANCZOS)
    return chart


def compose(chart, title, font_path):
    chart = chart.convert("RGBA")
    chart = scale_chart(chart, TARGET_WIDTH)
    chart_w, chart_h = chart.size

    try:
        font = ImageFont.truetype(font_path, TITLE_FONT_SIZE)
    except OSError:
        font = ImageFont.load_default()

    dummy = Image.new("RGBA", (1, 1))
    draw_dummy = ImageDraw.Draw(dummy)
    title_bbox = draw_dummy.textbbox((0, 0), title, font=font)
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]

    content_w = max(chart_w, title_w)
    content_h = title_h + GAP_TITLE_CHART + chart_h
    canvas_w = content_w + 2 * MARGIN
    canvas_h = content_h + 2 * MARGIN

    results = {}
    for variant, bg_color in [("dark", BG_COLOR_DARK), ("transparent", BG_COLOR_TRANSPARENT)]:
        canvas = Image.new("RGBA", (canvas_w, canvas_h), bg_color)
        draw = ImageDraw.Draw(canvas)

        title_x = (canvas_w - title_w) // 2
        title_y = MARGIN
        draw.text((title_x, title_y), title, font=font, fill=TITLE_COLOR)

        chart_x = (canvas_w - chart_w) // 2
        chart_y = MARGIN + title_h + GAP_TITLE_CHART
        canvas.paste(chart, (chart_x, chart_y), chart)

        if variant == "dark":
            canvas = round_corners(canvas, CORNER_RADIUS)

        results[variant] = canvas

    return results


def image_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# --- Streamlit UI ---
st.set_page_config(page_title="Chart Composer", layout="wide")
st.title("Chart Composer")
st.caption("Paste a chart from clipboard or upload a file, pick the fund, download branded PNGs.")

titles = load_titles()
fund_names = list(titles.keys())

col_left, col_right = st.columns([2, 1])

with col_right:
    fund = st.selectbox("Fund", fund_names, index=0)
    chart_title = titles.get(fund, "")
    chart_title = st.text_input("Chart title", value=chart_title)
    slug = to_slug(fund)

with col_left:
    paste_result = pib("Paste chart from clipboard", key="paste_btn")

    show_upload = st.toggle("Upload a file instead", value=False)
    uploaded = None
    if show_upload:
        uploaded = st.file_uploader("Upload chart image", type=["png", "jpg", "jpeg", "webp"])

# Resolve chart image from paste or upload
chart_img = None

if paste_result and paste_result.image_data:
    chart_img = paste_result.image_data
    st.image(chart_img, caption=f"Pasted: {chart_img.size[0]}x{chart_img.size[1]}", use_container_width=True)
elif uploaded:
    chart_img = Image.open(uploaded)
    st.image(chart_img, caption=f"Uploaded: {chart_img.size[0]}x{chart_img.size[1]}", use_container_width=True)

if chart_img and chart_title:
    if st.button("Compose", type="primary", use_container_width=True):
        with st.spinner("Composing..."):
            results = compose(chart_img, chart_title, FONT_PATH)

        col_dark, col_trans = st.columns(2)

        with col_dark:
            dark = results["dark"]
            st.image(dark, caption=f"Dark ({dark.size[0]}x{dark.size[1]})", use_container_width=True)
            st.download_button(
                "Download dark",
                data=image_to_bytes(dark),
                file_name=f"{slug}_dark.png",
                mime="image/png",
                use_container_width=True,
            )

        with col_trans:
            trans = results["transparent"]
            st.image(trans, caption=f"Transparent ({trans.size[0]}x{trans.size[1]})", use_container_width=True)
            st.download_button(
                "Download transparent",
                data=image_to_bytes(trans),
                file_name=f"{slug}_transparent.png",
                mime="image/png",
                use_container_width=True,
            )

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr(f"{slug}_dark.png", image_to_bytes(results["dark"]).read())
            zf.writestr(f"{slug}_transparent.png", image_to_bytes(results["transparent"]).read())
        zip_buf.seek(0)

        st.download_button(
            "Download both (zip)",
            data=zip_buf,
            file_name=f"{slug}_charts.zip",
            mime="application/zip",
            use_container_width=True,
        )
