from io import BytesIO
import os
from xml.sax.saxutils import escape

import streamlit as st
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
import google.generativeai as genai

# Setup Gemini API Direct-ah Streamlit-kulla
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


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
    if not api_key:
        st.error("GEMINI_API_KEY environment variable is missing!")
    else:
        prompt = f"""
        Generate a professional legal document with the following details:
        - Document Type: {document_type}
        - Parties Involved: {parties}
        - Terms & Conditions: {terms}
        - Effective Date: {dates}
        
        Please generate the entire formal document text clearly.
        """
        with st.spinner("Generating document..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                
                if response.text:
                    st.session_state["generated_doc"] = response.text
                    st.success("Document Generated Successfully!")
                else:
                    st.error("Failed to generate document. Please try again.")
            except Exception as e:
                st.error(f"Error generating document: {e}")

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