"""Entry point for the RAG Book application."""

from utils.logger import get_logger, setup_logging

# Initialize logging system
setup_logging()
logger = get_logger(__name__)


def main():
    """Run the RAG Book application.

    This is the primary entry point that bootstraps and starts
    the RAG pipeline. Currently prints a startup message.
    """
    logger.info("RAG Book application starting...")


if __name__ == "__main__":
    main()
