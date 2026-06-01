#!/usr/bin/env python3
"""
Example script demonstrating the Source Citations (Highest ROI) feature.

This script shows how to:
1. Initialize the citation manager
2. Generate responses with citation tracking
3. Display and analyze citation scores
"""

from voice_assistant.citation_manager import (
    init_citation_manager, 
    get_citation_manager,
    Citation
)
from voice_assistant.response_generation import generate_response
from voice_assistant.config import Config
from voice_assistant.api_key_manager import get_response_api_key
import json


def example_1_basic_citation_tracking():
    """Example 1: Basic citation tracking and ROI calculation."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Citation Tracking and ROI Calculation")
    print("="*70 + "\n")
    
    # Initialize citation manager
    citation_manager = init_citation_manager(top_k=5, min_roi_threshold=0.1)
    
    # Simulate retrieved documents
    retrieved_docs = [
        {
            "index": 0,
            "chunk": "Python is a high-level programming language...",
            "metadata": {"source": "python_guide.pdf", "page": 5},
            "score": 0.95
        },
        {
            "index": 1,
            "chunk": "Data structures in Python include lists, tuples, and dictionaries...",
            "metadata": {"source": "python_guide.pdf", "page": 12},
            "score": 0.87
        },
        {
            "index": 2,
            "chunk": "Machine learning frameworks like TensorFlow are built with Python...",
            "metadata": {"source": "ml_handbook.pdf", "page": 3},
            "score": 0.92
        }
    ]
    
    # Add retrieved documents
    citation_manager.add_retrieved_sources(retrieved_docs)
    print("✓ Added 3 retrieved documents")
    
    # Simulate citation usage
    citation_manager.track_citation_usage(chunk_ids=[0, 0, 2])
    print("✓ Tracked citation usage: Document 0 mentioned 2x, Document 2 mentioned 1x")
    
    # Get top citations
    top_citations = citation_manager.get_top_citations(by_roi=True)
    
    print("\n📚 Top Citations (Ranked by ROI):")
    print("-" * 70)
    for i, citation in enumerate(top_citations, 1):
        print(f"[{i}] {citation['source']}")
        print(f"    Relevance: {citation['relevance_score']:.4f}")
        print(f"    ROI Score: {citation['roi_score']:.4f}")
        print(f"    Mentions:  {citation['mention_count']}")
        print()
    
    # Get summary
    summary = citation_manager.get_summary()
    print("📊 Citation Summary:")
    print(f"   Total sources: {summary['total_sources']}")
    print(f"   Avg relevance: {summary['average_relevance']:.4f}")


def example_2_roi_calculation():
    """Example 2: Demonstrate ROI calculation formula."""
    print("\n" + "="*70)
    print("EXAMPLE 2: ROI Calculation Demonstration")
    print("="*70 + "\n")
    
    print("ROI Formula: Relevance × (1 + MentionCount × 0.2)\n")
    
    # Create sample citations
    samples = [
        {"name": "Source A", "relevance": 0.95, "mentions": 3},
        {"name": "Source B", "relevance": 0.95, "mentions": 0},
        {"name": "Source C", "relevance": 0.85, "mentions": 2},
        {"name": "Source D", "relevance": 0.80, "mentions": 1},
    ]
    
    results = []
    for sample in samples:
        rel = sample["relevance"]
        mentions = sample["mentions"]
        roi = rel * (1 + mentions * 0.2)
        results.append((sample["name"], rel, mentions, roi))
    
    # Sort by ROI
    results.sort(key=lambda x: x[3], reverse=True)
    
    print("Ranking by ROI (Highest First):\n")
    for rank, (name, rel, mentions, roi) in enumerate(results, 1):
        print(f"{rank}. {name}")
        print(f"   Relevance: {rel:.2f}")
        print(f"   Mentions:  {mentions}")
        print(f"   ROI:       {roi:.4f} ← Ranking metric")
        print()


def example_3_response_generation_with_citations():
    """Example 3: Generate a response with citation tracking."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Response Generation with Citations")
    print("="*70 + "\n")
    
    # Initialize citation manager
    citation_manager = init_citation_manager(top_k=3)
    
    # Example retrieved documents
    retrieved_docs = [
        {
            "index": 0,
            "chunk": "Artificial Intelligence is transforming industries...",
            "metadata": {"source": "ai_trends.pdf", "page": 1},
            "score": 0.98
        },
        {
            "index": 1,
            "chunk": "Machine learning models require large datasets for training...",
            "metadata": {"source": "ml_guide.pdf", "page": 15},
            "score": 0.89
        }
    ]
    
    citation_manager.add_retrieved_sources(retrieved_docs)
    
    # Simulate a response that references the sources
    mock_response = """
    Artificial Intelligence is revolutionizing technology. Machine learning, a subset 
    of AI, uses algorithms to learn from data. [1] The effectiveness of machine learning 
    models depends heavily on having sufficient training data. [2] Modern applications 
    combine multiple AI techniques to achieve better results. [1]
    """
    
    # Track citations mentioned in response
    citation_manager.track_citation_usage(response_text=mock_response)
    
    # Get results
    top_citations = citation_manager.get_top_citations(by_roi=True)
    summary = citation_manager.get_summary()
    
    print("Generated Response:")
    print("-" * 70)
    print(mock_response)
    
    print("\n📚 Top Citations Used:")
    print("-" * 70)
    for i, citation in enumerate(top_citations, 1):
        print(f"[{i}] {citation['source']}")
        print(f"    ROI: {citation['roi_score']:.4f} (Relevance: {citation['relevance_score']:.4f}, Mentions: {citation['mention_count']})")
    
    print(f"\n📊 Statistics:")
    print(f"   Average Relevance: {summary['average_relevance']:.4f}")


def example_4_configuration_options():
    """Example 4: Configure citation display settings."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Configuration Options")
    print("="*70 + "\n")
    
    print("Current Citation Settings:")
    print("-" * 70)
    print(f"ENABLE_SOURCE_CITATIONS:      {Config.ENABLE_SOURCE_CITATIONS}")
    print(f"TOP_CITATIONS_TO_DISPLAY:     {Config.TOP_CITATIONS_TO_DISPLAY}")
    print(f"MIN_ROI_THRESHOLD:            {Config.MIN_ROI_THRESHOLD}")
    print(f"INCLUDE_CITATION_SCORES:      {Config.INCLUDE_CITATION_SCORES}")
    print(f"MAX_SOURCE_PREVIEW_LENGTH:    {Config.MAX_SOURCE_PREVIEW_LENGTH}")
    
    print("\n\nCustomization Examples:")
    print("-" * 70)
    
    print("\n1. Show only top 3 citations:")
    print("   Config.TOP_CITATIONS_TO_DISPLAY = 3")
    
    print("\n2. Filter low-quality sources:")
    print("   Config.MIN_ROI_THRESHOLD = 0.5")
    
    print("\n3. Hide numerical scores:")
    print("   Config.INCLUDE_CITATION_SCORES = False")
    
    print("\n4. Disable citations completely:")
    print("   Config.ENABLE_SOURCE_CITATIONS = False")


def example_5_citation_context_format():
    """Example 5: Citation context format for system prompts."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Citation Context Format")
    print("="*70 + "\n")
    
    citation_manager = init_citation_manager()
    
    retrieved_docs = [
        {
            "index": 0,
            "chunk": "Climate change is one of the most pressing issues of our time.",
            "metadata": {"source": "climate_report.pdf", "page": 1},
            "score": 0.96
        },
        {
            "index": 1,
            "chunk": "Global temperatures have risen by approximately 1.1°C since pre-industrial times.",
            "metadata": {"source": "climate_report.pdf", "page": 5},
            "score": 0.92
        }
    ]
    
    citation_manager.add_retrieved_sources(retrieved_docs)
    context = citation_manager.get_citation_context()
    
    print("Citation Context for System Prompt:")
    print("-" * 70)
    print(context)


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("Source Citations (Highest ROI) Feature - Examples")
    print("="*70)
    
    try:
        example_1_basic_citation_tracking()
        example_2_roi_calculation()
        example_3_response_generation_with_citations()
        example_4_configuration_options()
        example_5_citation_context_format()
        
        print("\n" + "="*70)
        print("✅ All examples completed successfully!")
        print("="*70 + "\n")
        
        print("Next Steps:")
        print("1. Review SOURCE_CITATIONS_FEATURE.md for detailed documentation")
        print("2. Review CITATIONS_QUICKSTART.md for quick reference")
        print("3. Customize Config settings based on your needs")
        print("4. Monitor citation quality in your application")
        print()
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
