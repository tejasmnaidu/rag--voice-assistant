from fastembed import TextEmbedding

_model = None

def get_embedding(text: str) -> list[float]:
    """
    Get the embedding for a given text using FastEmbed (local ONNX pipeline).
    This runs completely locally and avoids any rate limit or billing issues.
    """
    global _model
    if _model is None:
        _model = TextEmbedding("BAAI/bge-small-en-v1.5")
    
    # Clean text to avoid problems with line breaks
    text = text.replace("\n", " ")
    
    # Generate embedding
    embedding = list(_model.embed([text]))[0]
    return embedding.tolist()
