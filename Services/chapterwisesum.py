import os
import re




def generate_chapter_name(text: str, default_prefix="Chapter"):
    """Generate a chapter name from the first few words if no heading is detected."""
    # Take first 5–10 words for naming
    snippet = " ".join(text.split()[:10])
    snippet = snippet.rstrip(".").strip()
    return f"{default_prefix}: {snippet}"

def split_into_chapters_smart(text: str):
    """
    Splits PDF into chapters based on headings or keywords.
    Auto-generates chapter names if heading is missing.
    """
    # Regex for headings (Chapter 1, CHAPTER I, 1. Introduction, etc.)
    pattern = re.compile(
        r'(Chapter\s*\d+\s*[:\-–]?\s*[\w\s]+|CHAPTER\s+[IVXLCDM]+\s*[:\-–]?\s*[\w\s]+|\d+\.\s*[\w\s]+)',
        flags=re.IGNORECASE
    )
    
    matches = list(pattern.finditer(text))
    chapters = []

    if matches:
        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            title = match.group().strip()
            content = text[start:end].strip()
            # If content is empty, generate name from next few words
            if not content:
                title = generate_chapter_name(text[start:end])
            chapters.append((title, content))
    else:
        # No headings detected, split text roughly by ~3000 words per chapter
        words = text.split()
        chunk_size = 3000
        for i in range(0, len(words), chunk_size):
            content = " ".join(words[i:i+chunk_size])
            title = generate_chapter_name(content, default_prefix=f"Chapter {(i//chunk_size)+1}")
            chapters.append((title, content))
    
    return chapters