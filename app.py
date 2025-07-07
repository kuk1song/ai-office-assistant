import streamlit as st
import os
from src.main import process_file
from src.document_parser import parse_document # To display images

def main():
    st.set_page_config(page_title="AI Office Assistant", page_icon="🤖")

    st.title("🤖 Mini SIAE - AI Office Assistant")
    st.write("Welcome! Upload your PDF or DOCX document to get a comprehensive analysis, including a summary, key points, and insights from text, tables, and images.")

    uploaded_file = st.file_uploader("Choose a document...", type=["pdf", "docx", "txt"])

    if uploaded_file is not None:
        # To process the file, we need to save it to a temporary location
        # because our parser currently works with file paths.
        temp_dir = "temp_uploads"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.info(f"Processing `{uploaded_file.name}`... Please wait.")

        # Display a spinner while processing
        with st.spinner("Analyzing the document... This may take a moment."):
            # Call the core processing logic from src/main.py
            analysis_result = process_file(temp_file_path)

        st.success("Analysis complete!")

        # Display the analysis result
        st.markdown("---")
        st.markdown(analysis_result)

        # Display extracted images for context
        # We re-parse to get image paths, could be optimized later
        parsed_data = parse_document(temp_file_path)
        image_paths = parsed_data.get("image_paths", [])

        if image_paths:
            st.markdown("---")
            st.subheader("Extracted Images for Reference")
            for img_path in image_paths:
                try:
                    st.image(img_path, caption=os.path.basename(img_path), use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not display image {os.path.basename(img_path)}: {e}")

        # Clean up the temporary file and directories
        os.remove(temp_file_path)


if __name__ == '__main__':
    main() 