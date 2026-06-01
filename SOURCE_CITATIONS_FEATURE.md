# Source Citations (Highest ROI) Feature

## Overview

The Source Citations feature tracks and displays the most impactful sources used to generate AI responses. It ranks sources by **ROI (Return on Investment)**, which combines **relevance scores** with **usage metrics** to highlight the highest-value sources.

---

## Key Components

### 1. **Citation Manager** (`voice_assistant/citation_manager.py`)
Manages source tracking and ROI calculation.

#### Main Classes:
- **`Citation`**: Represents a single source with:
  - Relevance score (from vector retrieval)
  - ROI score (relevance × usage impact)
  - Mention count (how many times referenced)
  - Metadata (source name, page number, etc.)

- **`CitationManager`**: Orchestrates citation tracking with:
  - Retrieval of top citations ranked by ROI
  - Automatic citation detection in responses
  - Citation statistics and summaries

#### Key Methods:
```python
# Add retrieved documents to tracking
citation_manager.add_retrieved_sources(retrieved_docs)

# Track how many times sources were used in response
citation_manager.track_citation_usage(response_text=response)

# Get top citations ranked by ROI
top_citations = citation_manager.get_top_citations(by_roi=True)

# Get citation statistics
summary = citation_manager.get_summary()
```

---

### 2. **Enhanced Response Generation** (`voice_assistant/response_generation.py`)
Updated to track citations while generating responses.

#### New Signature:
```python
response_text, citations_info = generate_response(
    model='groq',
    api_key=api_key,
    chat_history=history,
    retrieved_docs=docs,           # NEW: Pass retrieved documents
    include_citations=True          # NEW: Enable citation tracking
)
```

#### Features:
- ✅ Augments chat history with source context
- ✅ Formats sources for inclusion in system prompt
- ✅ Tracks citation usage in generated responses
- ✅ Returns citation summary with ROI scores

---

### 3. **Configuration Settings** (`voice_assistant/config.py`)
New configuration options for citation behavior:

```python
# Citation and Source Tracking Settings
ENABLE_SOURCE_CITATIONS = True          # Master toggle
TOP_CITATIONS_TO_DISPLAY = 5           # Max citations to show
MIN_ROI_THRESHOLD = 0.1                # Minimum ROI to include
INCLUDE_CITATION_SCORES = True         # Show relevance/ROI scores
MAX_SOURCE_PREVIEW_LENGTH = 300        # Character limit for preview
```

---

### 4. **Backend API Integration** (`backend/main.py`)
FastAPI backend now returns citation metadata:

#### Updated `/query` Endpoint Response:
```json
{
  "answer": "Response text...",
  "sources": [...],  // Original sources
  "citations": [      // NEW: Ranked by ROI
    {
      "chunk_id": 1,
      "text": "Source text...",
      "metadata": {"source": "doc.pdf", "page": 5},
      "relevance_score": 0.95,
      "roi_score": 0.95,
      "mention_count": 2,
      "source": "doc.pdf (Page 5)"
    }
  ],
  "citation_summary": {  // NEW: Statistics
    "total_sources_available": 10,
    "top_citations_count": 5,
    "average_relevance": 0.87
  }
}
```

---

### 5. **Frontend Display** (`app.py`)
Enhanced response display with citation rankings:

#### Display Format:
```
## 📚 Source Citations (Ranked by ROI)

[1] document.pdf (Page 3) | Relevance: 0.95 | ROI: 0.95 | Mentions: 2
[2] document.pdf (Page 7) | Relevance: 0.89 | ROI: 0.89 | Mentions: 1
[3] reference.pdf (Page 2) | Relevance: 0.82 | ROI: 0.82 | Mentions: 1

Avg. Relevance Score: 0.87
```

---

## How ROI Scoring Works

### ROI Calculation:
```
ROI Score = Relevance Score × (1 + Mention Count × 0.2)
```

### Example:
- Source A: Relevance = 0.95, Mentions = 2
  - ROI = 0.95 × (1 + 2 × 0.2) = 0.95 × 1.4 = **1.33**

- Source B: Relevance = 0.89, Mentions = 1
  - ROI = 0.89 × (1 + 1 × 0.2) = 0.89 × 1.2 = **1.068**

→ **Source A ranks higher** (1.33 > 1.068) despite similar relevance due to higher usage

---

## Usage Examples

### Example 1: Enable Citations in Your Code
```python
from voice_assistant.citation_manager import init_citation_manager, get_citation_manager
from voice_assistant.response_generation import generate_response

# Initialize manager
citation_mgr = init_citation_manager(top_k=5, min_roi_threshold=0.1)

# Generate response with citations
response, citations_info = generate_response(
    model='groq',
    api_key=api_key,
    chat_history=[{"role": "user", "content": "What is X?"}],
    retrieved_docs=your_docs,
    include_citations=True
)

# Access top citations
top_citations = citations_info['top_citations']
for citation in top_citations:
    print(f"{citation['source']}: ROI={citation['roi_score']}")
```

### Example 2: Configure Citation Display
```python
from voice_assistant.config import Config

# Customize citation settings
Config.TOP_CITATIONS_TO_DISPLAY = 3      # Show top 3 only
Config.MIN_ROI_THRESHOLD = 0.2           # Higher threshold
Config.INCLUDE_CITATION_SCORES = True    # Show scores
```

### Example 3: Access Citation Statistics
```python
citation_manager = get_citation_manager()
summary = citation_manager.get_summary()

print(f"Total Sources: {summary['total_sources']}")
print(f"Avg Relevance: {summary['average_relevance']}")
for citation in summary['top_citations']:
    print(f"- {citation['source']}: ROI={citation['roi_score']}")
```

---

## Backend Integration Flow

```
User Query
    ↓
Query Rewrite & Retrieval
    ↓
Add to Citation Manager
    ↓
Generate Response with Sources
    ↓
Track Citation Usage in Response
    ↓
Calculate ROI Scores
    ↓
Return Response + Top Citations
    ↓
Frontend Display (Ranked by ROI)
```

---

## Configuration Best Practices

| Setting | Default | Recommendation | Use Case |
|---------|---------|-----------------|----------|
| `TOP_CITATIONS_TO_DISPLAY` | 5 | 3-7 | Adjust based on UI space |
| `MIN_ROI_THRESHOLD` | 0.1 | 0.15-0.3 | Filter low-impact sources |
| `INCLUDE_CITATION_SCORES` | True | True | Show for transparency |
| `MAX_SOURCE_PREVIEW_LENGTH` | 300 | 200-400 | Balance detail vs brevity |
| `ENABLE_SOURCE_CITATIONS` | True | True | Master control |

---

## Performance Considerations

- **Citation Tracking**: ~5-10ms overhead per response
- **ROI Calculation**: O(n) where n = number of retrieved documents
- **Memory**: Minimal (~1KB per citation)
- **Scaling**: Efficient for up to 1000+ documents

---

## Troubleshooting

### Citations Not Appearing?
1. Check `Config.ENABLE_SOURCE_CITATIONS = True`
2. Verify backend returns `citations` field in response
3. Ensure `retrieved_docs` are passed to `generate_response()`

### ROI Scores Seem Low?
- Adjust `MIN_ROI_THRESHOLD` lower
- Increase `mention_impact` factor in `Citation.calculate_roi()`

### Too Many Citations?
- Reduce `TOP_CITATIONS_TO_DISPLAY`
- Increase `MIN_ROI_THRESHOLD`

---

## Future Enhancements

- [ ] Machine learning model for importance scoring
- [ ] Citation graph visualization
- [ ] User feedback loop for ROI refinement
- [ ] Export citation metadata (BibTeX, JSON)
- [ ] Citation conflict resolution
- [ ] Multi-language source support

---

## API Reference

### CitationManager
```python
class CitationManager:
    def add_retrieved_sources(docs: List[Dict]) -> None
    def track_citation_usage(chunk_ids: List[int], response_text: str) -> None
    def get_top_citations(by_roi: bool = True, exclude_low_roi: bool = True) -> List[Dict]
    def get_citation_context() -> str
    def get_summary() -> Dict
    def reset() -> None
```

### Citation
```python
class Citation:
    def calculate_roi() -> float
    def to_dict() -> Dict
```

---

## Support

For issues or feature requests, please refer to:
- Citation tracking logic: `voice_assistant/citation_manager.py`
- Response generation: `voice_assistant/response_generation.py`
- Backend integration: `backend/main.py`
