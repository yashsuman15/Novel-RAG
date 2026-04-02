from llm.model import LLM_lite

class QueryExpander:
    def __init__(self):
        self.llm_lite = LLM_lite()

    def expand(self, query: str, num_queries: int = 10) -> list[str]:
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
