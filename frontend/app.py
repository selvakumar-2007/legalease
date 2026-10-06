from io import BytesIO
from xml.sax.saxutils import escape

import streamlit as st
import requests
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def create_docx(document_text: str) -> bytes:
    document = Document()
    for line in document_text.splitlines():
        document.add_paragraph(line)

    output = BytesIO()
    document.save(output)
    return output.getvalue()


def create_pdf(document_text: str) -> bytes:
    output = BytesIO()
    pdf = SimpleDocTemplate(
        output,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "DocumentBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceAfter=8,
    )
    content = []
    for line in document_text.splitlines():
        if line.strip():
            content.append(Paragraph(escape(line), body_style))
        else:
            content.append(Spacer(1, 8))

    if not content:
        content.append(Paragraph("", body_style))
    pdf.build(content)
    return output.getvalue()

st.set_page_config(page_title="LegalEase", layout="centered")
st.title("LegalEase: AI Legal Document Generator")

document_type = st.text_input("Document Type (e.g., Agreement, Contract, NDA)")
parties = st.text_area("Parties Involved")
terms = st.text_area("Terms & Conditions")
dates = st.text_input("Effective Date")

if st.button("Generate Document"):
    payload = {
        "document_type": document_type,
        "parties": parties,
        "terms": terms,
        "dates": dates
    }
    with st.spinner("Generating document..."):
        try:
            res = requests.post("http://localhost:8000/generate", json=payload, timeout=60)
            data = res.json() if res.content else {}

            if res.status_code == 200 and "document" in data:
                st.session_state["generated_doc"] = data["document"]
                st.success("Document Generated Successfully!")
            elif res.status_code == 429:
                st.error(
                    "Gemini API quota for this key/project is exhausted. "
                    "Wait for the quota to reset, or use a key/project with available quota."
                )
            elif res.status_code == 401:
                st.error(
                    "The Gemini API key is invalid or unauthorized. Add a valid key "
                    "to the project's .env file, then restart the backend."
                )
            else:
                error_message = data.get("detail") or data.get("error") or "Error generating document"
                st.error(f"Error generating document: {error_message}")
        except requests.RequestException as e:
            st.error(f"Failed to connect to backend: {e}")

if "generated_doc" in st.session_state:
    st.subheader("Generated Document")
    edited_text = st.text_area("Edit Document Below:", st.session_state["generated_doc"], height=300)

    text_col, docx_col, pdf_col = st.columns(3)
    with text_col:
        st.download_button(
            label="Download as .TXT",
            data=edited_text,
            file_name="legal_document.txt",
            mime="text/plain",
        )
    with docx_col:
        st.download_button(
            label="Download as .DOCX",
            data=create_docx(edited_text),
            file_name="legal_document.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    with pdf_col:
        st.download_button(
            label="Download as .PDF",
            data=create_pdf(edited_text),
            file_name="legal_document.pdf",
            mime="application/pdf",
        )