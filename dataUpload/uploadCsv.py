import pandas as pd
from .extractData import extract

def allowed_file(filename, allowed_extensions):
    """Check if the uploaded file is a CSV."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def process_csv(filepath, category):
    """
    Process the CSV file based on the selected category.

    Args:
        filepath (str): The path to the saved CSV file.
        category (str): The selected category ("additional", "registrar", or "admissions").

    Returns:
        str: Success message.
    """
    # Read the CSV file
    df = pd.read_csv(filepath, encoding='latin-1')

    # Process based on category
    if category == 'additional':
        clean = extract(cols=["","",""],category='additional',data=df) 
            
    elif category == 'registrar':
        clean = extract(category='registrar',data=df)
    elif category == 'admissions':
        clean = extract(category='admissions',data=df)
    else:
        raise ValueError("Invalid category provided")
    
    return f"File processed successfully under the category: {category}"

