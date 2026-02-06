import pandas as pd
import pypdf
import io

def extract_text_from_file(file_storage):
    """
    Extracts text/data from the uploaded Flask FileStorage object.
    Supports .csv, .xlsx, .pdf
    """
    filename = file_storage.filename.lower()
    
    try:
        if filename.endswith('.csv'):
            file_storage.seek(0)
            df = pd.read_csv(file_storage)
            return df.to_markdown(index=False)
        
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(file_storage)
            return df.to_markdown(index=False)
        
        elif filename.endswith('.pdf'):
            reader = pypdf.PdfReader(file_storage)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
            
        else:
            return "Unsupported file format."
            
    except Exception as e:
        print(f"⚠️ DATA EXTRACTION ERROR: {e}")
        return f"Error reading file: {str(e)}"
