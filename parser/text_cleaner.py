import re

def clean_text(text: str) -> str:
    """Cleans and normalizes raw text extracted from PDF."""
    if not text:
        return ""
    
    # Replace non-breaking spaces and vertical tabs with normal spaces
    text = text.replace('\xa0', ' ').replace('\v', '\n')
    
    # Replace smart quotes and special hyphens
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")  # en-dash and em-dash
    
    # Remove multiple consecutive spaces (but keep line structure)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Reduce excessive newlines to at most two
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()
