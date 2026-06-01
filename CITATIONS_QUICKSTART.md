# Source Citations Feature - Quick Start Guide

## What's New?

Your RAG Voice Assistant now displays sources ranked by **ROI (Return on Investment)**. This means you see the most impactful sources first - those that are both relevant AND actually used in generating responses.

---

## For Users

### What You'll See
After each AI response, you'll now see:

```
📚 Source Citations (Ranked by ROI)

[1] document.pdf (Page 3) | Relevance: 0.95 | ROI: 0.95 | Mentions: 2
[2] reference.pdf (Page 7) | Relevance: 0.89 | ROI: 0.89 | Mentions: 1
[3] guide.pdf (Page 2) | Relevance: 0.82 | ROI: 0.82 | Mentions: 1

Avg. Relevance Score: 0.87
```

### Understanding the Scores
- **Relevance**: How well the source matches your query (0-1 scale)
- **ROI**: Return on Investment - relevance × usage impact
- **Mentions**: How many times this source influenced the answer

---

## For Developers

### Enable Citations
```python
from voice_assistant.config import Config

# Ensure citations are enabled (default is True)
Config.ENABLE_SOURCE_CITATIONS = True
```

### Customize Display
```python
# Show fewer citations
Config.TOP_CITATIONS_TO_DISPLAY = 3

# Only show high-quality sources
Config.MIN_ROI_THRESHOLD = 0.25

# Hide numerical scores
Config.INCLUDE_CITATION_SCORES = False
```

### Access Citation Data Programmatically
```python
from voice_assistant.response_generation import generate_response

response_text, citations_info = generate_response(
    model='groq',
    api_key=api_key,
    chat_history=history,
    retrieved_docs=docs,
    include_citations=True
)

# Get top citations
top_citations = citations_info['top_citations']
print(f"Found {len(top_citations)} top citations")

for citation in top_citations:
    print(f"- {citation['source']}: ROI={citation['roi_score']}")
```

### Backend Integration
The FastAPI backend automatically returns enhanced citation data:

```json
{
  "citations": [
    {
      "chunk_id": 1,
      "source": "document.pdf (Page 3)",
      "relevance_score": 0.95,
      "roi_score": 0.95,
      "mention_count": 2
    }
  ],
  "citation_summary": {
    "total_sources_available": 10,
    "top_citations_count": 3,
    "average_relevance": 0.92
  }
}
```

---

## ROI Scoring Formula

```
ROI = Relevance × (1 + MentionCount × 0.2)
```

**Example:**
- Source with relevance 0.95, mentioned 2 times: ROI = 0.95 × 1.4 = **1.33**
- Source with relevance 0.95, mentioned 0 times: ROI = 0.95 × 1.0 = **0.95**

Higher mention count = Higher ROI = Better ranking

---

## Configuration Reference

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `ENABLE_SOURCE_CITATIONS` | True | Master toggle for citations |
| `TOP_CITATIONS_TO_DISPLAY` | 5 | Max citations shown |
| `MIN_ROI_THRESHOLD` | 0.1 | Minimum ROI to display |
| `INCLUDE_CITATION_SCORES` | True | Show numerical scores |
| `MAX_SOURCE_PREVIEW_LENGTH` | 300 | Character limit for previews |

---

## Common Tasks

### Disable Citations
```python
Config.ENABLE_SOURCE_CITATIONS = False
```

### Show Only Top 3 Citations
```python
Config.TOP_CITATIONS_TO_DISPLAY = 3
```

### Filter Low-Quality Sources
```python
Config.MIN_ROI_THRESHOLD = 0.3  # Only high ROI sources
```

### Hide Scores for Cleaner Display
```python
Config.INCLUDE_CITATION_SCORES = False
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No citations showing | Check `ENABLE_SOURCE_CITATIONS = True` |
| Too many citations | Reduce `TOP_CITATIONS_TO_DISPLAY` or increase `MIN_ROI_THRESHOLD` |
| Scores look wrong | Verify retrieved documents are passed to `generate_response()` |
| Backend errors | Ensure citation manager initialized on startup |

---

## File Locations

- **Citation Logic**: `voice_assistant/citation_manager.py`
- **Response Generation**: `voice_assistant/response_generation.py`
- **Configuration**: `voice_assistant/config.py`
- **Backend API**: `backend/main.py`
- **Frontend Display**: `app.py` (line ~430)
- **Full Documentation**: `SOURCE_CITATIONS_FEATURE.md`

---

## Next Steps

1. ✅ Run the app normally - citations will show automatically
2. 🔧 Customize settings in `Config` class if needed
3. 📊 Monitor citation quality and adjust `MIN_ROI_THRESHOLD` as needed
4. 📝 See `SOURCE_CITATIONS_FEATURE.md` for advanced usage

---

Happy citing! 📚
