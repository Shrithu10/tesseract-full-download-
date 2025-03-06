import streamlit as st
import requests
from PyPDF2 import PdfMerger
import os
import re
import base64

def sanitize_filename(filename):
    filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', "", filename)
    return filename

def download_pdf(url, filename):
    response = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(response.content)

def merge_pdfs(pdf_list, output):
    merger = PdfMerger()
    for pdf in pdf_list:
        merger.append(pdf)
    merger.write(output)
    merger.close()

def generate_download_link(file_path, file_label):
    with open(file_path, "rb") as file:
        base64_pdf = base64.b64encode(file.read()).decode('utf-8')
    file_name = os.path.basename(file_path)
    download_link = f'<a href="data:application/octet-stream;base64,{base64_pdf}" download="{file_name}">{file_label}</a>'
    return download_link

def main():
    st.title("Download and Merge PDFs from Tess")
    auth_key = st.text_input("Enter Authorization Key", type="password")
    unit_id = st.text_input("Enter Unit ID")
    custom_filename = st.text_input("Enter Desired Name for Merged PDF (e.g., Merged_Document.pdf)", "Merged_Document.pdf")
    
    if st.button("Download PDFs"):
        if not auth_key or not unit_id:
            st.error("Please enter both Authorization Key and Unit ID.")
            return

        url = f"https://api.tesseractonline.com/studentmaster/get-topics-unit/{unit_id}"
        headers = {"Authorization": auth_key}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            st.error("Failed to fetch data from API. Please check the Authorization Key and Unit ID.")
            return

        data = response.json()

        if data.get("Error", True):
            st.error("Error in API response. Please check the Authorization Key and Unit ID.")
            return

        topics = data.get("payload", {}).get("topics", [])
        if not topics:
            st.warning("No topics found in the given unit.")
            return

        pdf_files = []
        output_dir = "pdfs"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for topic in topics:
            pdf_url = topic.get("pdf")
            if pdf_url:
                full_pdf_url = f"https://api.tesseractonline.com/{pdf_url}"
                filename = sanitize_filename(f"{topic.get('name', 'topic')}.pdf")
                filepath = os.path.join(output_dir, filename)
                download_pdf(full_pdf_url, filepath)
                pdf_files.append(filepath)

        if pdf_files:
            # Ensure the custom filename has a .pdf extension
            if not custom_filename.lower().endswith('.pdf'):
                custom_filename += '.pdf'
            
            output_file = os.path.join(output_dir, sanitize_filename(custom_filename))
            merge_pdfs(pdf_files, output_file)

            download_link = generate_download_link(output_file, f"Click here to download the merged PDF")
            st.markdown(download_link, unsafe_allow_html=True)

            st.success("PDFs downloaded and merged successfully!")
        else:
            st.warning("No PDFs found to download.")

if __name__ == "__main__":
    main()
