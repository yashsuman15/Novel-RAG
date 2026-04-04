"""System prompt templates for LLM interactions.

Contains pre-defined system messages used by the LLM clients to set
the behavioural context for different tasks (answer generation,
query expansion, and reranking).
"""

SYS_MSG = """Answer the question based on the provided context. If you don't know the answer, say you don't know. Always use all the information in the context to answer the question."""

SYS_MSG_QUERY_EXPANDER = """You are a helpful assistant.You will always do the task as you were asked.You generate search queries. Return only queries, one per line."""

SYS_MSG_RERANKER = """You are a helpful assistant.You will always do the task as you were asked.You rerank the search results. Return only the reranked results, one per line."""
