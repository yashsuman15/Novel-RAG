"""Query expansion module for the retrieval pipeline.

Provides :class:`QueryExpander` which uses a lightweight LLM to
generate multiple reformulations of a user query, improving recall
during vector similarity search.
"""

from llm.model import LLM_lite


class QueryExpander:
    """Expand a single user query into multiple search queries.

    Uses :class:`~llm.model.LLM_lite` to generate diverse
    reformulations of the original query, each approaching the topic
    from a different angle. The expanded set is used for multi-query
    retrieval to improve recall.

    Attributes:
        llm_lite: The lightweight LLM instance used for expansion.

    Example:
        >>> expander = QueryExpander()
        >>> queries = expander.expand("Who is Orsted?", num_queries=3)
        >>> print(queries)
        ['Who is Orsted?', 'What role does Orsted play...', ...]
    """

    def __init__(self):
        """Initialize the query expander with a lightweight LLM."""
        self.llm_lite = LLM_lite()

    def expand(self, query: str, num_queries: int = 10) -> list[str]:
        """Expand a query into multiple diverse search queries.

        Generates ``num_queries`` alternative formulations and prepends
        the original query to the result list.

        Args:
            query: The original user query to expand.
            num_queries: Number of additional queries to generate.
                Defaults to ``10``.

        Returns:
            A list of strings starting with the original query followed
            by up to ``num_queries`` expanded variants.
        """
        prompt = f"""Generate {num_queries} different search queries to find relevant
information for this question. Each query should approach the topic
from a different angle. Return ONLY the queries, one per line, no numbering.

Question: {query}"""

        response = self.llm_lite.generate(prompt)

        queries = [q.strip() for q in response.strip().split("\n") if q.strip()]
        return [query] + queries[:num_queries]  # original query + expanded queries


if __name__ == "__main__":
    query_expander = QueryExpander()
    queries = query_expander.expand("why does orsted hate hitogami?")
    for query in queries:
        print(query)
