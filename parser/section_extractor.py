import re
from typing import List, Dict, Any

def extract_sections(clean_text: str) -> Dict[str, Any]:
    """
    Parses the text of the RBI circular into main paragraphs and detailed amendments.
    """
    paragraphs = []
    amendments = []
    
    # 1. Identify main numbered paragraph starts (e.g., "2. ", "3. ", "4. ")
    # Find the positions where numbered paragraphs start
    para_matches = list(re.finditer(r"\n\s*(\d+)\.\s+", "\n" + clean_text))
    
    if para_matches:
        # Paragraph 1 is everything before paragraph 2
        p1_end = para_matches[0].start()
        p1_text = clean_text[:p1_end].strip()
        if p1_text:
            paragraphs.append({"id": "1", "text": p1_text})
            
        # Parse paragraphs between the matches
        for idx in range(len(para_matches)):
            start_pos = para_matches[idx].start()
            para_id = para_matches[idx].group(1)
            
            # The end position is either the next paragraph start or the end of the text
            if idx + 1 < len(para_matches):
                end_pos = para_matches[idx + 1].start()
            else:
                end_pos = len("\n" + clean_text)
                
            # Extract paragraph text (accounting for the prepended newline)
            para_text = ("\n" + clean_text)[start_pos:end_pos].strip()
            # Strip the leading number (e.g. "2. ")
            para_text_clean = re.sub(r"^\d+\.\s+", "", para_text)
            
            paragraphs.append({
                "id": para_id,
                "text": para_text_clean
            })
    else:
        # If no numbered paragraphs are found, treat the whole document as paragraph 1
        paragraphs.append({"id": "1", "text": clean_text})

    # 2. Extract detailed amendments
    # Amendments are usually sub-points under the paragraph that contains the word "amended" or "amendment"
    amendment_para = None
    for para in paragraphs:
        if "amended" in para["text"].lower() or "substituted" in para["text"].lower():
            amendment_para = para
            break
            
    # If we found the paragraph containing the amendments
    if amendment_para:
        text_to_search = amendment_para["text"]
        # Find sub-points starting with e.g. (i), (ii), (iii), (a), (b), etc. at the start of a paragraph/line
        sub_matches = list(re.finditer(r"(?:\n|^)\s*\(([a-zA-Z0-9]+)\)\s+", text_to_search))
        
        for idx in range(len(sub_matches)):
            start_pos = sub_matches[idx].start()
            sub_id = sub_matches[idx].group(1)
            
            if idx + 1 < len(sub_matches):
                end_pos = sub_matches[idx + 1].start()
            else:
                end_pos = len(text_to_search)
                
            sub_text = text_to_search[start_pos:end_pos].strip()
            # Strip the leading sub-id (e.g., "(i) ")
            sub_text_clean = re.sub(r"^\([a-zA-Z0-9]+\)\s+", "", sub_text)
            
            amendments.append({
                "id": sub_id,
                "text": sub_text_clean
            })
            
    return {
        "paragraphs": paragraphs,
        "amendments": amendments
    }
