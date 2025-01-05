import ssl
import nltk
from nltk.tokenize import sent_tokenize

# Disable SSL certificate verification
ssl._create_default_https_context = ssl._create_unverified_context
nltk.download('punkt_tab')

# Splits text into smaller chunks (up to 500 tokens) for efficient processing by the LLM.
# Uses sentence tokenization via nltk.
def split_text_into_chunks(text, max_tokens=500):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []

    for sentence in sentences:
        if sum(len(word) for word in current_chunk) + len(sentence.split()) <= max_tokens:
            current_chunk.append(sentence)
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks