import re
import pdfplumber
# -------------------------first page text reader----------------------


def read_first_page(file):

    text = ""

    with pdfplumber.open(file) as pdf:

        page = pdf.pages[0]

        words = page.extract_words(
            x_tolerance=1,
            y_tolerance=1,
            keep_blank_chars=False,
            use_text_flow=True
        )

        current_line = []
        last_top = None

        for word in words:

            if last_top is None:
                last_top = word["top"]

            if abs(word["top"] - last_top) > 5:
                text += " ".join(current_line) + "\n"
                current_line = []
                last_top = word["top"]

            current_line.append(word["text"])

        if current_line:
            text += " ".join(current_line) + "\n"

    return text


# -------------------Getting unit code and name----------------


def extract_unit_details(text):

    pattern = pattern = r'\b([A-Z]{2,5}\s\d{4})\s+(.+?)\s+LAST\s+REVISION'

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if match:

        return {
            "unit_code": match.group(1).strip(),
            "unit_name": match.group(2).strip()
        }

    return {
        "unit_code": None,
        "unit_name": None
    }
