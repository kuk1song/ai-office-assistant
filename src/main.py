import os
import argparse
import shutil
from dotenv import load_dotenv
from .document_parser import parse_document
from .ai_analyzer import analyze_document

# Load environment variables
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(project_root, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

def process_file(file_path: str):
    """
    Orchestrates the analysis of a single file.
    This function will be called by the UI.
    """
    print("--- Starting AI Office Assistant ---")
    print(f"Parsing document from: {file_path}")

    # Step 1: Parse the document to get text and images
    parsed_data = parse_document(file_path)

    if "error" in parsed_data:
        error_message = f"Error: {parsed_data['error']}"
        print(error_message)
        return error_message

    text_content = parsed_data.get("text", "")
    image_paths = parsed_data.get("image_paths", [])

    # Step 2: Analyze the entire document (text, tables, and images) at once
    print("\n--- Analyzing Document ---")
    analysis_result = analyze_document(text_content, image_paths)
    print(analysis_result)
        
    # Clean up the temporary image directory
    temp_dir = "temp_images"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    print("\n--- End of Analysis ---")
    return analysis_result

def main():
    """Main function to run the document analysis from the command line."""
    parser = argparse.ArgumentParser(description="Analyze a document (PDF, DOCX, or TXT) using AI.")
    parser.add_argument("file_path", type=str, help="The path to the document file to analyze.")
    args = parser.parse_args()
    
    process_file(args.file_path)


if __name__ == '__main__':
    main() 