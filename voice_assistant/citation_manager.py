# voice_assistant/citation_manager.py

import logging
from typing import List, Dict, Tuple
import re

logger = logging.getLogger(__name__)


class Citation:
    """Represents a single source citation with relevance metrics."""
    
    def __init__(self, chunk_id: int, text: str, metadata: Dict = None, 
                 relevance_score: float = 0.0, roi_score: float = 0.0, 
                 mention_count: int = 0):
        """
        Initialize a citation.
        
        Args:
            chunk_id: Unique identifier for the chunk
            text: The source text content
            metadata: Metadata associated with the source (file name, page number, etc.)
            relevance_score: Initial relevance score from retriever
            roi_score: ROI score based on usage in response
            mention_count: How many times this source was referenced
        """
        self.chunk_id = chunk_id
        self.text = text
        self.metadata = metadata or {}
        self.relevance_score = relevance_score
        self.roi_score = roi_score
        self.mention_count = mention_count
    
    def calculate_roi(self) -> float:
        """Calculate Return on Investment score for this citation."""
        # ROI = relevance_score * mention_impact
        # Higher mention count increases ROI
        mention_impact = 1.0 + (self.mention_count * 0.2)
        self.roi_score = self.relevance_score * mention_impact
        return self.roi_score
    
    def to_dict(self) -> Dict:
        """Convert citation to dictionary format."""
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "metadata": self.metadata,
            "relevance_score": round(self.relevance_score, 4),
            "roi_score": round(self.roi_score, 4),
            "mention_count": self.mention_count,
            "source": self._format_source()
        }
    
    def _format_source(self) -> str:
        """Format source information for display."""
        if "source" in self.metadata:
            source = self.metadata["source"]
            page = self.metadata.get("page", "")
            if page:
                return f"{source} (Page {page})"
            return source
        return f"Chunk {self.chunk_id}"


class CitationManager:
    """Manages source citations for RAG responses with ROI ranking."""
    
    def __init__(self, top_k: int = 5, min_roi_threshold: float = 0.1):
        """
        Initialize citation manager.
        
        Args:
            top_k: Number of top citations to return
            min_roi_threshold: Minimum ROI score to include a citation
        """
        self.top_k = top_k
        self.min_roi_threshold = min_roi_threshold
        self.citations: Dict[int, Citation] = {}
    
    def add_retrieved_sources(self, retrieved_docs: List[Dict]) -> None:
        """
        Add retrieved documents as potential citations.
        
        Args:
            retrieved_docs: List of documents from retriever with metadata
        """
        for doc in retrieved_docs:
            chunk_id = doc.get("index", 0)
            text = doc.get("chunk", "")
            metadata = doc.get("metadata", {})
            score = doc.get("score", 0.0)
            
            self.citations[chunk_id] = Citation(
                chunk_id=chunk_id,
                text=text,
                metadata=metadata,
                relevance_score=score,
                roi_score=score
            )
    
    def track_citation_usage(self, chunk_ids: List[int] = None, 
                            response_text: str = "") -> None:
        """
        Track how many times each citation was used/referenced in the response.
        
        Args:
            chunk_ids: Explicit list of chunk IDs to track
            response_text: Response text to analyze for source references
        """
        if chunk_ids:
            for chunk_id in chunk_ids:
                if chunk_id in self.citations:
                    self.citations[chunk_id].mention_count += 1
        
        # Auto-detect references in response (e.g., "[1]", "[source 1]", etc.)
        if response_text:
            self._analyze_response_citations(response_text)
    
    def _analyze_response_citations(self, response_text: str) -> None:
        """
        Analyze response text for citation patterns and update mention counts.
        
        Args:
            response_text: The generated response to analyze
        """
        # Look for patterns like [1], [source1], (source), etc.
        patterns = [
            r'\[\d+\]',  # [1], [2], etc.
            r'\[source\s+\d+\]',  # [source 1], etc.
            r'\(source\s+\d+\)',  # (source 1), etc.
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for match in matches:
                try:
                    # Extract number from match
                    num = re.search(r'\d+', match)
                    if num:
                        chunk_id = int(num.group())
                        if chunk_id in self.citations:
                            self.citations[chunk_id].mention_count += 1
                except (ValueError, AttributeError):
                    continue
    
    def get_top_citations(self, by_roi: bool = True, 
                         exclude_low_roi: bool = True) -> List[Dict]:
        """
        Get top citations ranked by ROI or relevance score.
        
        Args:
            by_roi: If True, rank by ROI; if False, rank by relevance
            exclude_low_roi: If True, exclude citations below min_roi_threshold
        
        Returns:
            List of top citations as dictionaries
        """
        # Calculate ROI for all citations
        for citation in self.citations.values():
            citation.calculate_roi()
        
        # Filter if needed
        filtered_citations = self.citations.values()
        if exclude_low_roi:
            filtered_citations = [c for c in filtered_citations 
                                 if c.roi_score >= self.min_roi_threshold]
        
        # Sort and limit
        sort_key = lambda c: c.roi_score if by_roi else c.relevance_score
        sorted_citations = sorted(filtered_citations, key=sort_key, reverse=True)
        
        return [c.to_dict() for c in sorted_citations[:self.top_k]]
    
    def get_citation_context(self) -> str:
        """
        Generate a formatted string of all citations for including in prompts.
        
        Returns:
            Formatted citation context for system prompt
        """
        citations_list = []
        for idx, citation in enumerate(self.citations.values(), 1):
            citations_list.append(
                f"[{idx}] {citation._format_source()}:\n{citation.text[:200]}..."
            )
        
        return "\n\n".join(citations_list) if citations_list else ""
    
    def reset(self) -> None:
        """Clear all tracked citations."""
        self.citations.clear()
    
    def get_summary(self) -> Dict:
        """
        Get a summary of citation statistics.
        
        Returns:
            Dictionary with citation statistics
        """
        if not self.citations:
            return {"total_sources": 0, "top_citations": []}
        
        top_citations = self.get_top_citations(by_roi=True)
        
        return {
            "total_sources": len(self.citations),
            "top_citations": top_citations,
            "average_relevance": sum(c.relevance_score for c in self.citations.values()) / len(self.citations)
        }


# Global citation manager instance
_default_citation_manager = None


def init_citation_manager(top_k: int = 5, min_roi_threshold: float = 0.1) -> CitationManager:
    """Initialize the global citation manager."""
    global _default_citation_manager
    _default_citation_manager = CitationManager(top_k=top_k, min_roi_threshold=min_roi_threshold)
    return _default_citation_manager


def get_citation_manager() -> CitationManager:
    """Get the global citation manager, creating it if necessary."""
    global _default_citation_manager
    if _default_citation_manager is None:
        _default_citation_manager = CitationManager()
    return _default_citation_manager
