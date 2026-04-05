"""Unit tests for validation schemas.

Tests cover:
- QueryRequest validation and sanitization
- XSS injection detection and prevention
- Field constraints and validation rules
- Whitespace normalization
- Optional field handling
- SourceInfo validation
- Edge cases and error handling
"""

import pytest
from pydantic import ValidationError

from schemas.validation import DocumentIngestRequest, QueryRequest, QueryResponse, SourceInfo


class TestQueryRequest:
    """Tests for QueryRequest schema."""

    def test_valid_query(self, sample_query):
        """Test that valid query is accepted."""
        request = QueryRequest(query=sample_query)
        assert request.query == sample_query
        assert request.top_k is None
        assert request.num_queries is None

    def test_query_with_optional_fields(self):
        """Test query with optional field overrides."""
        request = QueryRequest(query="Test query", top_k=5, num_queries=3)
        assert request.query == "Test query"
        assert request.top_k == 5
        assert request.num_queries == 3

    def test_query_whitespace_normalization(self):
        """Test that excessive whitespace is normalized."""
        request = QueryRequest(query="Who  is    Rudeus   Greyrat?")
        assert request.query == "Who is Rudeus Greyrat?"

    def test_query_leading_trailing_whitespace(self):
        """Test that leading/trailing whitespace is removed."""
        request = QueryRequest(query="  Who is Rudeus?  ")
        assert request.query == "Who is Rudeus?"

    def test_query_multiple_spaces_normalized(self):
        """Test that multiple spaces are collapsed to single space."""
        request = QueryRequest(query="Who     is     Rudeus?")
        assert request.query == "Who is Rudeus?"

    def test_query_tabs_and_newlines_normalized(self):
        """Test that tabs and newlines are normalized."""
        request = QueryRequest(query="Who\tis\nRudeus?")
        assert request.query == "Who is Rudeus?"

    def test_empty_query_rejected(self):
        """Test that empty query is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(query="")
        error_msg = str(exc_info.value)
        assert "query" in error_msg.lower()

    def test_whitespace_only_query_rejected(self):
        """Test that whitespace-only query is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(query="     ")
        error_msg = str(exc_info.value)
        assert "empty" in error_msg.lower() or "whitespace" in error_msg.lower()

    def test_query_min_length(self):
        """Test that single character query is accepted."""
        request = QueryRequest(query="a")
        assert request.query == "a"

    def test_query_max_length(self):
        """Test that query at max length is accepted."""
        long_query = "a" * 2000
        request = QueryRequest(query=long_query)
        assert len(request.query) == 2000

    def test_query_too_long_rejected(self):
        """Test that queries exceeding max length are rejected."""
        long_query = "a" * 2001
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(query=long_query)
        error_msg = str(exc_info.value)
        assert "2000" in error_msg or "max_length" in error_msg.lower()

    def test_xss_script_tag_rejected(self):
        """Test that script tags are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(query="<script>alert('xss')</script>")
        error_msg = str(exc_info.value)
        assert "dangerous" in error_msg.lower()

    def test_xss_script_tag_uppercase_rejected(self):
        """Test that uppercase SCRIPT tags are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(query="<SCRIPT>alert('xss')</SCRIPT>")
        error_msg = str(exc_info.value)
        assert "dangerous" in error_msg.lower()

    def test_xss_javascript_protocol_rejected(self):
        """Test that javascript: protocol is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(query="javascript:alert('xss')")
        error_msg = str(exc_info.value)
        assert "dangerous" in error_msg.lower()

    def test_xss_javascript_protocol_uppercase_rejected(self):
        """Test that uppercase JAVASCRIPT: protocol is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(query="JAVASCRIPT:alert('xss')")
        error_msg = str(exc_info.value)
        assert "dangerous" in error_msg.lower()

    def test_xss_event_handler_rejected(self):
        """Test that HTML event handlers are rejected."""
        dangerous_queries = [
            "<img onerror='alert(1)'>",
            "<div onclick='alert(1)'>",
            "<body onload='alert(1)'>",
            "' onmouseover='alert(1)'",
        ]
        for query in dangerous_queries:
            with pytest.raises(ValidationError) as exc_info:
                QueryRequest(query=query)
            error_msg = str(exc_info.value)
            assert "dangerous" in error_msg.lower()

    def test_safe_html_entities_accepted(self):
        """Test that safe queries with HTML-like content are accepted."""
        # These should pass - they're just text, not actual HTML
        safe_queries = [
            "What is a <vector> in mathematics?",
            "Explain the > operator",
            "What does x < y mean?",
        ]
        for query in safe_queries:
            request = QueryRequest(query=query)
            assert request.query == query

    def test_top_k_valid_range(self):
        """Test that top_k within valid range is accepted."""
        for k in [1, 10, 25, 50]:
            request = QueryRequest(query="test", top_k=k)
            assert request.top_k == k

    def test_top_k_minimum_constraint(self):
        """Test that top_k must be at least 1."""
        with pytest.raises(ValidationError):
            QueryRequest(query="test", top_k=0)

    def test_top_k_maximum_constraint(self):
        """Test that top_k cannot exceed 50."""
        with pytest.raises(ValidationError):
            QueryRequest(query="test", top_k=51)

    def test_top_k_negative_rejected(self):
        """Test that negative top_k is rejected."""
        with pytest.raises(ValidationError):
            QueryRequest(query="test", top_k=-5)

    def test_num_queries_valid_range(self):
        """Test that num_queries within valid range is accepted."""
        for n in [1, 5, 10, 20]:
            request = QueryRequest(query="test", num_queries=n)
            assert request.num_queries == n

    def test_num_queries_minimum_constraint(self):
        """Test that num_queries must be at least 1."""
        with pytest.raises(ValidationError):
            QueryRequest(query="test", num_queries=0)

    def test_num_queries_maximum_constraint(self):
        """Test that num_queries cannot exceed 20."""
        with pytest.raises(ValidationError):
            QueryRequest(query="test", num_queries=21)

    def test_num_queries_negative_rejected(self):
        """Test that negative num_queries is rejected."""
        with pytest.raises(ValidationError):
            QueryRequest(query="test", num_queries=-3)

    def test_all_fields_together(self):
        """Test valid request with all fields specified."""
        request = QueryRequest(query="Who is Rudeus Greyrat?", top_k=15, num_queries=7)
        assert request.query == "Who is Rudeus Greyrat?"
        assert request.top_k == 15
        assert request.num_queries == 7


class TestSourceInfo:
    """Tests for SourceInfo schema."""

    def test_valid_source_info_complete(self):
        """Test that valid source info with all fields is accepted."""
        source = SourceInfo(
            citation_number=1,
            source="data/raw/volume1.pdf",
            page=42,
            content="Sample content from the source.",
        )
        assert source.citation_number == 1
        assert source.source == "data/raw/volume1.pdf"
        assert source.page == 42
        assert source.content == "Sample content from the source."

    def test_source_info_without_page(self):
        """Test source info with optional page field omitted."""
        source = SourceInfo(
            citation_number=1, source="data/raw/volume1.pdf", content="Sample content"
        )
        assert source.citation_number == 1
        assert source.page is None
        assert source.content == "Sample content"

    def test_source_info_page_none(self):
        """Test source info with page explicitly set to None."""
        source = SourceInfo(
            citation_number=2, source="data/raw/volume2.pdf", page=None, content="Content"
        )
        assert source.page is None

    def test_citation_number_positive(self):
        """Test that citation numbers are positive integers."""
        for num in [1, 5, 100, 999]:
            source = SourceInfo(citation_number=num, source="test.pdf", content="Test content")
            assert source.citation_number == num

    def test_source_path_variations(self):
        """Test various source path formats."""
        paths = [
            "data/raw/volume1.pdf",
            "/absolute/path/to/document.pdf",
            "relative/path/doc.pdf",
            "C:\\Windows\\path\\file.pdf",
        ]
        for path in paths:
            source = SourceInfo(citation_number=1, source=path, content="Test")
            assert source.source == path

    def test_content_can_be_long(self):
        """Test that content field can handle long text."""
        long_content = "A" * 5000
        source = SourceInfo(citation_number=1, source="test.pdf", content=long_content)
        assert len(source.content) == 5000


class TestQueryResponse:
    """Tests for QueryResponse schema."""

    def test_valid_query_response(self):
        """Test that valid query response is accepted."""
        sources = [
            SourceInfo(
                citation_number=1,
                source="data/raw/volume1.pdf",
                page=10,
                content="Test content",
            )
        ]
        response = QueryResponse(
            query="Who is Rudeus?",
            answer="Rudeus Greyrat is the protagonist.",
            sources=sources,
            thinking="Analysis of the query...",
        )
        assert response.query == "Who is Rudeus?"
        assert response.answer == "Rudeus Greyrat is the protagonist."
        assert len(response.sources) == 1
        assert response.thinking == "Analysis of the query..."

    def test_query_response_without_thinking(self):
        """Test query response with optional thinking field omitted."""
        sources = [SourceInfo(citation_number=1, source="test.pdf", content="Content")]
        response = QueryResponse(query="Test?", answer="Answer", sources=sources)
        assert response.thinking is None

    def test_query_response_empty_sources(self):
        """Test that query response can have empty sources list."""
        response = QueryResponse(query="Test?", answer="No sources found.", sources=[])
        assert len(response.sources) == 0

    def test_query_response_multiple_sources(self):
        """Test query response with multiple sources."""
        sources = [
            SourceInfo(citation_number=i, source=f"vol{i}.pdf", content=f"Content {i}")
            for i in range(1, 6)
        ]
        response = QueryResponse(
            query="Complex question?", answer="Detailed answer", sources=sources
        )
        assert len(response.sources) == 5
        assert all(isinstance(s, SourceInfo) for s in response.sources)


class TestDocumentIngestRequest:
    """Tests for DocumentIngestRequest schema."""

    def test_valid_document_ingest_request(self):
        """Test that valid ingest request is accepted."""
        request = DocumentIngestRequest(file_path="data/raw/volume1.pdf")
        assert request.file_path == "data/raw/volume1.pdf"
        assert request.chunk_size is None
        assert request.chunk_overlap is None

    def test_ingest_request_with_overrides(self):
        """Test ingest request with optional field overrides."""
        request = DocumentIngestRequest(
            file_path="data/raw/volume1.pdf", chunk_size=800, chunk_overlap=200
        )
        assert request.file_path == "data/raw/volume1.pdf"
        assert request.chunk_size == 800
        assert request.chunk_overlap == 200

    def test_ingest_request_chunk_size_validation(self):
        """Test that chunk_size must be in valid range."""
        # Valid
        request = DocumentIngestRequest(file_path="test.pdf", chunk_size=1000)
        assert request.chunk_size == 1000

        # Too low
        with pytest.raises(ValidationError):
            DocumentIngestRequest(file_path="test.pdf", chunk_size=50)

        # Too high
        with pytest.raises(ValidationError):
            DocumentIngestRequest(file_path="test.pdf", chunk_size=6000)

    def test_ingest_request_chunk_overlap_validation(self):
        """Test that chunk_overlap must be in valid range."""
        # Valid
        request = DocumentIngestRequest(file_path="test.pdf", chunk_overlap=200)
        assert request.chunk_overlap == 200

        # Negative
        with pytest.raises(ValidationError):
            DocumentIngestRequest(file_path="test.pdf", chunk_overlap=-10)

        # Too high
        with pytest.raises(ValidationError):
            DocumentIngestRequest(file_path="test.pdf", chunk_overlap=1500)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_unicode_query(self):
        """Test that unicode characters in queries are handled correctly."""
        unicode_queries = [
            "What is 日本語?",
            "Explain Москва",
            "What does café mean?",
            "Who is 中国人?",
        ]
        for query in unicode_queries:
            request = QueryRequest(query=query)
            assert request.query == query

    def test_special_characters_in_query(self):
        """Test that special characters are handled correctly."""
        special_queries = [
            "What is $100?",
            "Explain @mention",
            "What does #hashtag mean?",
            "Who uses & symbol?",
        ]
        for query in special_queries:
            request = QueryRequest(query=query)
            assert request.query == query

    def test_numeric_query(self):
        """Test that numeric queries are accepted."""
        request = QueryRequest(query="123")
        assert request.query == "123"

    def test_punctuation_only_query(self):
        """Test that punctuation-only queries are accepted."""
        request = QueryRequest(query="???")
        assert request.query == "???"

    def test_mixed_case_xss_detection(self):
        """Test that XSS detection is case-insensitive."""
        mixed_case_attacks = [
            "<ScRiPt>alert(1)</ScRiPt>",
            "JaVaScRiPt:alert(1)",
            "<img OnErRoR='alert(1)'>",
        ]
        for attack in mixed_case_attacks:
            with pytest.raises(ValidationError) as exc_info:
                QueryRequest(query=attack)
            assert "dangerous" in str(exc_info.value).lower()
