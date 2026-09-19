import io
import re
import fitz
import streamlit as st


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="PDF Formatter",
    page_icon="📄",
    layout="wide",
)

st.title("📄 PDF Formatter")

# ADDED — TOP DESCRIPTION
st.markdown(
    "Format your PDF easily — remove old borders, add new borders, "
    "customize pages, preview changes, and download the final PDF."
)

st.caption(
    "Clean the PDF, add the new format, preview every page, "
    "then customize individual pages."
)

MM = 72 / 25.4


def pt(mm_value):
    return mm_value * MM


# =========================================================
# PAGE RANGE PARSER
# =========================================================

def parse_pages(value, total_pages):
    """
    Examples:
        1
        1,2,5
        1-5
        1,3,7-10
    """

    pages = set()

    if not value:
        return pages

    for part in value.split(","):

        part = part.strip()

        if not part:
            continue

        if "-" in part:

            try:
                start, end = part.split("-", 1)

                start = int(start.strip())
                end = int(end.strip())

                if start > end:
                    start, end = end, start

                for number in range(start, end + 1):

                    if 1 <= number <= total_pages:
                        pages.add(number)

            except ValueError:
                pass

        else:

            try:
                number = int(part)

                if 1 <= number <= total_pages:
                    pages.add(number)

            except ValueError:
                pass

    return pages


# =========================================================
# REMOVE OLD PAGE NUMBERS
# =========================================================

def remove_old_page_numbers(page, page_index):

    page_no = page_index + 1

    W = page.rect.width
    H = page.rect.height

    redactions = []

    # Search individual words.
    for word in page.get_text("words"):

        x0, y0, x1, y1, text = word[:5]

        text = text.strip()

        if y0 < H * 0.78:
            continue

        center_x = (x0 + x1) / 2

        if abs(center_x - W / 2) > W * 0.35:
            continue

        if text == str(page_no):

            redactions.append(
                fitz.Rect(
                    x0 - 6,
                    y0 - 5,
                    x1 + 6,
                    y1 + 5
                )
            )

    # Search blocks for "Page 12", "Page-12", etc.
    for block in page.get_text("blocks"):

        x0, y0, x1, y1, text = block[:5]

        if y0 < H * 0.78:
            continue

        clean = " ".join(text.split())

        pattern = re.compile(
            rf"^(page[\s\-:]*)?{page_no}$",
            re.IGNORECASE
        )

        if pattern.fullmatch(clean):

            redactions.append(
                fitz.Rect(
                    x0 - 6,
                    y0 - 5,
                    x1 + 6,
                    y1 + 5
                )
            )

    for rect in redactions:
        page.add_redact_annot(
            rect,
            fill=(1, 1, 1)
        )


# =========================================================
# REMOVE OLD VECTOR BORDERS
# =========================================================

def remove_old_borders(page):

    W = page.rect.width
    H = page.rect.height

    for drawing in page.get_drawings():

        r = drawing["rect"]

        width = r.width
        height = r.height

        left = (
            r.x0 <= 70
            and height >= H * 0.65
            and width <= 50
        )

        right = (
            r.x1 >= W - 70
            and height >= H * 0.65
            and width <= 50
        )

        top = (
            r.y0 <= 50
            and width >= W * 0.65
            and height <= 12
        )

        bottom = (
            r.y1 >= H - 50
            and width >= W * 0.65
            and height <= 12
        )

        if left or right or top or bottom:

            page.add_redact_annot(
                fitz.Rect(
                    r.x0 - 4,
                    r.y0 - 4,
                    r.x1 + 4,
                    r.y1 + 4
                ),
                fill=(1, 1, 1)
            )


# =========================================================
# STEP 1
# =========================================================

def clean_pdf(pdf_bytes):

    doc = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    for i, page in enumerate(doc):

        remove_old_page_numbers(
            page,
            i
        )

        remove_old_borders(
            page
        )

        page.apply_redactions(
            images=fitz.PDF_REDACT_IMAGE_PIXELS,
            graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED,
            text=fitz.PDF_REDACT_TEXT_REMOVE
        )

    result = io.BytesIO()

    doc.save(
        result,
        garbage=4,
        deflate=True
    )

    doc.close()

    return result.getvalue()


# =========================================================
# DRAW BORDER
# =========================================================

def draw_border(page, margin_mm, border_design):

    margin = pt(margin_mm)

    border = fitz.Rect(
        margin,
        margin,
        page.rect.width - margin,
        page.rect.height - margin
    )

    # =====================================================
    # DESIGN 1 — SINGLE LINE
    # =====================================================

    if border_design == "Single Line":

        page.draw_rect(
            border,
            color=(0, 0, 0),
            width=0.8
        )

    # =====================================================
    # DESIGN 2 — DOUBLE LINE
    # =====================================================

    elif border_design == "Double Line":

        page.draw_rect(
            border,
            color=(0, 0, 0),
            width=0.8
        )

        inner = fitz.Rect(
            margin + pt(3),
            margin + pt(3),
            page.rect.width - margin - pt(3),
            page.rect.height - margin - pt(3)
        )

        page.draw_rect(
            inner,
            color=(0, 0, 0),
            width=0.8
        )

    # =====================================================
    # DESIGN 3 — THICK OUTER + THIN INNER
    # =====================================================

    elif border_design == "Thick Outer + Thin Inner":

        page.draw_rect(
            border,
            color=(0, 0, 0),
            width=2.2
        )

        inner = fitz.Rect(
            margin + pt(4),
            margin + pt(4),
            page.rect.width - margin - pt(4),
            page.rect.height - margin - pt(4)
        )

        page.draw_rect(
            inner,
            color=(0, 0, 0),
            width=0.7
        )

    # =====================================================
    # DESIGN 4 — TRIPLE LINE
    # =====================================================

    elif border_design == "Triple Line":

        page.draw_rect(
            border,
            color=(0, 0, 0),
            width=0.8
        )

        inner1 = fitz.Rect(
            margin + pt(2.5),
            margin + pt(2.5),
            page.rect.width - margin - pt(2.5),
            page.rect.height - margin - pt(2.5)
        )

        inner2 = fitz.Rect(
            margin + pt(5),
            margin + pt(5),
            page.rect.width - margin - pt(5),
            page.rect.height - margin - pt(5)
        )

        page.draw_rect(
            inner1,
            color=(0, 0, 0),
            width=0.6
        )

        page.draw_rect(
            inner2,
            color=(0, 0, 0),
            width=0.6
        )

    # =====================================================
    # DESIGN 5 — DOTTED
    # =====================================================

    elif border_design == "Dotted":

        page.draw_rect(
            border,
            color=(0, 0, 0),
            width=0.8,
            dashes="[1 3]"
        )

    # =====================================================
    # DESIGN 6 — DASHED
    # =====================================================

    elif border_design == "Dashed":

        page.draw_rect(
            border,
            color=(0, 0, 0),
            width=0.8,
            dashes="[6 4]"
        )


# =========================================================
# ADD TITLE
# =========================================================

def add_title(
    page,
    title,
    margin_mm,
    position,
    vertical_offset,
    font_size
):

    margin = pt(margin_mm)

    horizontal_left = margin + pt(5)
    horizontal_right = page.rect.width - margin - pt(5)

    # Above/below the top border.
    border_y = margin

    if position == "Above border":
        base_y = border_y - pt(10)
    else:
        base_y = border_y + pt(2)

    # Positive value moves UP.
    y = base_y - pt(vertical_offset)

    box = fitz.Rect(
        horizontal_left,
        y,
        horizontal_right,
        y + pt(8)
    )

    page.insert_textbox(
        box,
        title,
        fontsize=font_size,
        fontname="helv",
        align=fitz.TEXT_ALIGN_RIGHT,
        color=(0, 0, 0)
    )


# =========================================================
# ADD DEPARTMENT
# =========================================================

def add_department(
    page,
    margin_mm,
    position,
    vertical_offset,
    font_size
):

    margin = pt(margin_mm)

    horizontal_left = margin + pt(5)
    horizontal_right = page.rect.width / 2

    border_y = page.rect.height - margin

    if position == "Below border":
        base_y = border_y + pt(2)
    else:
        base_y = border_y - pt(9)

    # Positive = UP
    # Negative = DOWN
    y = base_y - pt(vertical_offset)

    box = fitz.Rect(
        horizontal_left,
        y,
        horizontal_right,
        y + pt(7)
    )

    page.insert_textbox(
        box,
        "DEPARTMENT OF EEE",
        fontsize=font_size,
        fontname="helv",
        align=fitz.TEXT_ALIGN_LEFT,
        color=(0, 0, 0)
    )


# =========================================================
# ADD PAGE NUMBER
# =========================================================

def add_page_number(
    page,
    page_number,
    margin_mm,
    position,
    vertical_offset,
    font_size
):

    margin = pt(margin_mm)

    horizontal_left = page.rect.width / 2
    horizontal_right = page.rect.width - margin - pt(5)

    border_y = page.rect.height - margin

    if position == "Below border":
        base_y = border_y + pt(2)
    else:
        base_y = border_y - pt(9)

    # Positive = UP
    # Negative = DOWN
    y = base_y - pt(vertical_offset)

    box = fitz.Rect(
        horizontal_left,
        y,
        horizontal_right,
        y + pt(7)
    )

    page.insert_textbox(
        box,
        f"Page {page_number}",
        fontsize=font_size,
        fontname="helv",
        align=fitz.TEXT_ALIGN_RIGHT,
        color=(0, 0, 0)
    )


# =========================================================
# CREATE FORMATTED PDF
# =========================================================

def create_pdf(
    cleaned_bytes,
    title,
    page_settings,
    content_scale
):

    source = fitz.open(
        stream=cleaned_bytes,
        filetype="pdf"
    )

    output = fitz.open()

    scale = content_scale / 100.0

    for i, source_page in enumerate(source):

        page_no = i + 1

        W = source_page.rect.width
        H = source_page.rect.height

        settings = page_settings[page_no]

        new_page = output.new_page(
            width=W,
            height=H
        )

        # ---------------------------------------------
        # ORIGINAL CONTENT
        # ---------------------------------------------

        center_x = W / 2
        center_y = H / 2

        scaled_w = W * scale
        scaled_h = H * scale

        content_rect = fitz.Rect(
            center_x - scaled_w / 2,
            center_y - scaled_h / 2,
            center_x + scaled_w / 2,
            center_y + scaled_h / 2
        )

        new_page.show_pdf_page(
            content_rect,
            source,
            i,
            keep_proportion=True
        )

        # ---------------------------------------------
        # BORDER
        # ---------------------------------------------

        if settings["border"]:

            draw_border(
                new_page,
                settings["border_margin"],
                settings["border_design"]
            )

        # ---------------------------------------------
        # TITLE
        # ---------------------------------------------

        if settings["title"]:

            add_title(
                new_page,
                title,
                settings["border_margin"],
                settings["title_position"],
                settings["title_vertical"],
                settings["title_size"]
            )

        # ---------------------------------------------
        # DEPARTMENT
        # ---------------------------------------------

        if settings["department"]:

            add_department(
                new_page,
                settings["border_margin"],
                settings["department_position"],
                settings["department_vertical"],
                settings["department_size"]
            )

        # ---------------------------------------------
        # PAGE NUMBER
        # ---------------------------------------------

        if settings["page_number"]:

            add_page_number(
                new_page,
                page_no,
                settings["border_margin"],
                settings["page_position"],
                settings["page_vertical"],
                settings["page_size"]
            )

    result = io.BytesIO()

    output.save(
        result,
        garbage=4,
        deflate=True
    )

    output.close()
    source.close()

    return result.getvalue()


# =========================================================
# RENDER ONE PAGE
# =========================================================

def render_page(pdf_bytes, page_number, zoom=0.8):

    doc = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    page_number = max(
        1,
        min(page_number, len(doc))
    )

    page = doc[page_number - 1]

    pix = page.get_pixmap(
        matrix=fitz.Matrix(
            zoom,
            zoom
        ),
        alpha=False
    )

    image = pix.tobytes("png")

    doc.close()

    return image


# =========================================================
# RENDER ENTIRE PDF
# =========================================================

def render_all_pages(pdf_bytes):

    doc = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    images = []

    for i, page in enumerate(doc):

        pix = page.get_pixmap(
            matrix=fitz.Matrix(0.45, 0.45),
            alpha=False
        )

        images.append(
            (
                i + 1,
                pix.tobytes("png")
            )
        )

    doc.close()

    return images


# =========================================================
# DEFAULT SETTINGS
# =========================================================

def default_page_settings(total_pages):

    settings = {}

    for page in range(1, total_pages + 1):

        settings[page] = {

            "border": True,
            "title": True,
            "department": True,
            "page_number": True,

            "border_margin": 12,

            # ADDED
            "border_design": "Single Line",

            "title_position": "Above border",
            "department_position": "Below border",
            "page_position": "Below border",

            "title_vertical": 0,
            "department_vertical": 0,
            "page_vertical": 0,

            "title_size": 9,
            "department_size": 9,
            "page_size": 9,
        }

    return settings


# =========================================================
# SESSION STATE
# =========================================================

if "cleaned_pdf" not in st.session_state:
    st.session_state.cleaned_pdf = None

if "step2_preview" not in st.session_state:
    st.session_state.step2_preview = None

if "step3_preview" not in st.session_state:
    st.session_state.step3_preview = None

if "page_settings" not in st.session_state:
    st.session_state.page_settings = None

if "final_pdf" not in st.session_state:
    st.session_state.final_pdf = None


# =========================================================
# UPLOAD
# =========================================================

uploaded = st.file_uploader(
    "Upload your PDF",
    type=["pdf"]
)


if uploaded:

    original_bytes = uploaded.getvalue()

    info = fitz.open(
        stream=original_bytes,
        filetype="pdf"
    )

    total_pages = len(info)

    info.close()

    if (
        st.session_state.page_settings is None
        or len(st.session_state.page_settings) != total_pages
    ):

        st.session_state.page_settings = (
            default_page_settings(total_pages)
        )


    st.success(
        f"{total_pages} pages loaded."
    )


    # =====================================================
    # STEP 1
    # =====================================================

    st.header(
        "STEP 1 — Remove Existing Borders & Page Numbers"
    )

    st.write(
        "First, the old digital borders and page numbers "
        "are removed automatically."
    )

    if st.button(
        "🧹 Remove Old Formatting + Preview",
        use_container_width=True
    ):

        with st.spinner(
            "Removing existing borders and page numbers..."
        ):

            st.session_state.cleaned_pdf = (
                clean_pdf(original_bytes)
            )

            # Reset later previews.
            st.session_state.step2_preview = None
            st.session_state.step3_preview = None
            st.session_state.final_pdf = None

        st.success(
            "Old formatting removed."
        )


    if st.session_state.cleaned_pdf:

        st.subheader(
            "STEP 1 — Entire PDF Preview"
        )

        st.caption(
            "Scroll through the complete cleaned PDF."
        )

        all_images = render_all_pages(
            st.session_state.cleaned_pdf
        )

        for page_number, image in all_images:

            st.image(
                image,
                caption=f"Cleaned Page {page_number}",
                width=260
            )


    # =====================================================
    # STEP 2
    # =====================================================

    st.header(
        "STEP 2 — Add Border First"
    )

    st.write(
        "A new border is added first. Then the title, "
        "department and page number are placed around it."
    )

    border_margin_default = st.slider(
        "Default border distance from page edge (mm)",
        min_value=5,
        max_value=30,
        value=12
    )

    # =====================================================
    # BORDER DESIGN — ADDED
    # =====================================================

    border_design = st.selectbox(
        "Border Design",
        [
            "Single Line",
            "Double Line",
            "Thick Outer + Thin Inner",
            "Triple Line",
            "Dotted",
            "Dashed"
        ],
        key="global_border_design"
    )

    title = st.text_input(
        "Project Title",
        placeholder="Enter the title of the project"
    )

    # -----------------------------------------------------
    # HEADER POSITION
    # -----------------------------------------------------

    st.subheader(
        "Project Title Position"
    )

    title_position = st.radio(
        "Place project title:",
        [
            "Above border",
            "Below border"
        ],
        horizontal=True,
        key="global_title_position"
    )

    # -----------------------------------------------------
    # DEPARTMENT POSITION
    # -----------------------------------------------------

    st.subheader(
        "DEPARTMENT OF EEE Position"
    )

    department_position = st.radio(
        "Place DEPARTMENT OF EEE:",
        [
            "Above border",
            "Below border"
        ],
        horizontal=True,
        key="global_department_position"
    )

    # -----------------------------------------------------
    # PAGE NUMBER POSITION
    # -----------------------------------------------------

    st.subheader(
        "Page Number Position"
    )

    page_position = st.radio(
        "Place page number:",
        [
            "Above border",
            "Below border"
        ],
        horizontal=True,
        key="global_page_position"
    )


    # =====================================================
    # APPLY STEP 2
    # =====================================================

    if st.button(
        "👁️ Preview Entire PDF — Step 2",
        use_container_width=True
    ):

        if not st.session_state.cleaned_pdf:

            st.warning(
                "Complete Step 1 first."
            )

            st.stop()

        if not title.strip():

            st.error(
                "Enter the project title first."
            )

            st.stop()

        # Apply global Step-2 settings.
        for page_number in range(
            1,
            total_pages + 1
        ):

            settings = st.session_state.page_settings[
                page_number
            ]

            settings["border"] = True
            settings["title"] = True
            settings["department"] = True
            settings["page_number"] = True

            settings["border_margin"] = (
                border_margin_default
            )

            # ADDED
            settings["border_design"] = (
                border_design
            )

            settings["title_position"] = (
                title_position
            )

            settings["department_position"] = (
                department_position
            )

            settings["page_position"] = (
                page_position
            )

            settings["title_vertical"] = 0
            settings["department_vertical"] = 0
            settings["page_vertical"] = 0

        st.session_state.step2_preview = create_pdf(
            st.session_state.cleaned_pdf,
            title,
            st.session_state.page_settings,
            100
        )

        st.success(
            "Step 2 preview created."
        )


    # =====================================================
    # SHOW ENTIRE STEP 2 PREVIEW
    # =====================================================

    if st.session_state.step2_preview:

        st.subheader(
            "STEP 2 — Entire PDF Preview"
        )

        st.caption(
            "Every page is shown below. Check the complete "
            "document before making page-specific changes."
        )

        images = render_all_pages(
            st.session_state.step2_preview
        )

        preview_columns = 3

        for start in range(
            0,
            len(images),
            preview_columns
        ):

            cols = st.columns(preview_columns)

            for column_index, column in enumerate(cols):

                image_index = (
                    start + column_index
                )

                if image_index >= len(images):
                    break

                page_number, image = images[
                    image_index
                ]

                with column:

                    st.image(
                        image,
                        caption=f"Page {page_number}",
                        use_container_width=True
                    )


    # =====================================================
    # STEP 3
    # =====================================================

    st.header(
        "STEP 3 — Select Specific Pages To Modify"
    )

    st.write(
        "Select the pages where you want to remove the "
        "border, title, department or page number."
    )

    selected_pages = st.multiselect(
        "Select page(s)",
        options=list(
            range(1, total_pages + 1)
        ),
        format_func=lambda x: f"Page {x}",
    )


    if selected_pages:

        st.info(
            "The settings below will be applied only to "
            "the selected page(s)."
        )

        # -------------------------------------------------
        # REMOVE ITEMS
        # -------------------------------------------------

        st.subheader(
            "Remove from selected pages"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            remove_border = st.checkbox(
                "Remove border",
                key="selected_remove_border"
            )

        with col2:

            remove_title = st.checkbox(
                "Remove title",
                key="selected_remove_title"
            )

        with col3:

            remove_department = st.checkbox(
                "Remove DEPARTMENT OF EEE",
                key="selected_remove_department"
            )

        with col4:

            remove_page_number = st.checkbox(
                "Remove page number",
                key="selected_remove_page"
            )


        # -------------------------------------------------
        # SPECIFIC PAGE BORDER SIZE
        # -------------------------------------------------

        st.subheader(
            "Border size for selected pages"
        )

        selected_border_margin = st.slider(
            "Border distance (mm)",
            min_value=5,
            max_value=30,
            value=12,
            key="selected_border_margin"
        )


        # -------------------------------------------------
        # VERTICAL TITLE POSITION
        # -------------------------------------------------

        st.subheader(
            "Project Title — Vertical Adjustment"
        )

        selected_title_vertical = st.slider(
            "Title vertical position (mm)",
            min_value=-30,
            max_value=30,
            value=0,
            step=1,
            key="selected_title_vertical"
        )

        st.caption(
            "Positive = move UP | Negative = move DOWN. "
            "Horizontal position is unchanged."
        )


        # -------------------------------------------------
        # VERTICAL DEPARTMENT POSITION
        # -------------------------------------------------

        st.subheader(
            "DEPARTMENT OF EEE — Vertical Adjustment"
        )

        selected_department_vertical = st.slider(
            "Department vertical position (mm)",
            min_value=-30,
            max_value=30,
            value=0,
            step=1,
            key="selected_department_vertical"
        )

        st.caption(
            "Positive = move UP | Negative = move DOWN. "
            "Horizontal position is unchanged."
        )


        # -------------------------------------------------
        # VERTICAL PAGE NUMBER POSITION
        # -------------------------------------------------

        st.subheader(
            "Page Number — Vertical Adjustment"
        )

        selected_page_vertical = st.slider(
            "Page number vertical position (mm)",
            min_value=-30,
            max_value=30,
            value=0,
            step=1,
            key="selected_page_vertical"
        )

        st.caption(
            "Positive = move UP | Negative = move DOWN. "
            "Horizontal position is unchanged."
        )


        # -------------------------------------------------
        # TEXT SIZE
        # -------------------------------------------------

        st.subheader(
            "Text Size"
        )

        selected_text_size = st.slider(
            "Title / Department / Page number size",
            min_value=7,
            max_value=14,
            value=9,
            step=1,
            key="selected_text_size"
        )


        # -------------------------------------------------
        # APPLY TO SELECTED PAGES
        # -------------------------------------------------

        if st.button(
            "✅ Apply Changes To Selected Pages",
            use_container_width=True
        ):

            for page_number in selected_pages:

                settings = (
                    st.session_state.page_settings[
                        page_number
                    ]
                )

                if remove_border:
                    settings["border"] = False

                if remove_title:
                    settings["title"] = False

                if remove_department:
                    settings["department"] = False

                if remove_page_number:
                    settings["page_number"] = False

                # Border size
                settings["border_margin"] = (
                    selected_border_margin
                )

                # Vertical positions
                settings["title_vertical"] = (
                    selected_title_vertical
                )

                settings["department_vertical"] = (
                    selected_department_vertical
                )

                settings["page_vertical"] = (
                    selected_page_vertical
                )

                # Text size
                settings["title_size"] = (
                    selected_text_size
                )

                settings["department_size"] = (
                    selected_text_size
                )

                settings["page_size"] = (
                    selected_text_size
                )

            st.success(
                "Changes applied to the selected pages."
            )


    # =====================================================
    # STEP 4
    # =====================================================

    st.header(
        "STEP 4 — Preview Entire PDF After Page Changes"
    )

    if st.button(
        "👁️ Preview Entire Updated PDF",
        use_container_width=True
    ):

        if not st.session_state.cleaned_pdf:

            st.warning(
                "Complete Step 1 first."
            )

            st.stop()

        if not title.strip():

            st.error(
                "Enter the project title first."
            )

            st.stop()

        st.session_state.step3_preview = create_pdf(
            st.session_state.cleaned_pdf,
            title,
            st.session_state.page_settings,
            100
        )

        st.success(
            "Updated entire-PDF preview created."
        )


    if st.session_state.step3_preview:

        st.subheader(
            "Entire Updated PDF"
        )

        images = render_all_pages(
            st.session_state.step3_preview
        )

        preview_columns = 3

        for start in range(
            0,
            len(images),
            preview_columns
        ):

            cols = st.columns(preview_columns)

            for column_index, column in enumerate(cols):

                image_index = (
                    start + column_index
                )

                if image_index >= len(images):
                    break

                page_number, image = images[
                    image_index
                ]

                with column:

                    st.image(
                        image,
                        caption=f"Page {page_number}",
                        use_container_width=True
                    )


    # =====================================================
    # STEP 5
    # =====================================================

    st.header(
        "STEP 5 — Final Content Scale"
    )

    final_content_scale = st.slider(
        "Original PDF content scale",
        min_value=70,
        max_value=110,
        value=100,
        step=1,
        format="%d%%"
    )

    st.caption(
        "100% = original size. Lower values make the "
        "original PDF content smaller."
    )

    if st.button(
        "👁️ Preview Final PDF",
        use_container_width=True
    ):

        if not st.session_state.cleaned_pdf:

            st.warning(
                "Complete Step 1 first."
            )

            st.stop()

        if not title.strip():

            st.error(
                "Enter the project title first."
            )

            st.stop()

        st.session_state.final_preview = create_pdf(
            st.session_state.cleaned_pdf,
            title,
            st.session_state.page_settings,
            final_content_scale
        )

        st.success(
            "Final preview created."
        )


    if "final_preview" in st.session_state:

        st.subheader(
            "FINAL ENTIRE PDF PREVIEW"
        )

        images = render_all_pages(
            st.session_state.final_preview
        )

        preview_columns = 3

        for start in range(
            0,
            len(images),
            preview_columns
        ):

            cols = st.columns(preview_columns)

            for column_index, column in enumerate(cols):

                image_index = (
                    start + column_index
                )

                if image_index >= len(images):
                    break

                page_number, image = images[
                    image_index
                ]

                with column:

                    st.image(
                        image,
                        caption=f"Page {page_number}",
                        use_container_width=True
                    )


    # =====================================================
    # FINAL GENERATION
    # =====================================================

    st.header(
        "STEP 6 — Generate Final PDF"
    )

    if st.button(
        "✨ Generate Final PDF",
        type="primary",
        use_container_width=True
    ):

        if not st.session_state.cleaned_pdf:

            st.warning(
                "Complete Step 1 first."
            )

            st.stop()

        if not title.strip():

            st.error(
                "Enter the project title first."
            )

            st.stop()

        with st.spinner(
            "Generating final PDF..."
        ):

            st.session_state.final_pdf = create_pdf(
                st.session_state.cleaned_pdf,
                title,
                st.session_state.page_settings,
                final_content_scale
            )

        st.success(
            "Final PDF generated successfully!"
        )


    if st.session_state.final_pdf:

        st.download_button(
            "⬇️ Download Final PDF",
            data=st.session_state.final_pdf,
            file_name="formatted_project.pdf",
            mime="application/pdf",
            use_container_width=True
        )
