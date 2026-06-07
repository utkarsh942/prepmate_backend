import fitz

def extract_text_from_pdf(file_data):
    extracted_text = ""

    pdf_document = fitz.open(
        stream=file_data,
        filetype="pdf"
    )

    for page in pdf_document:
        extracted_text+= page.get_text()

    return extracted_text    