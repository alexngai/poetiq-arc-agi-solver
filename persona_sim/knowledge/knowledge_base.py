"""
Knowledge base implementation using RAG for document indexing and retrieval.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    DirectoryLoader,
    UnstructuredMarkdownLoader,
)
from langchain_community.vectorstores import Chroma
from langchain_anthropic import AnthropicEmbeddings
from langchain.schema import Document

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    Knowledge base for storing and retrieving product information.
    Uses RAG (Retrieval Augmented Generation) with vector embeddings.
    """

    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "product_knowledge",
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize the knowledge base.

        Args:
            persist_directory: Directory to persist the vector database
            collection_name: Name of the collection in the vector database
            anthropic_api_key: API key for Anthropic embeddings
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        self.embeddings = AnthropicEmbeddings(
            api_key=self.anthropic_api_key,
            model="voyage-3",
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        self.vectorstore: Optional[Chroma] = None

    def load_documents_from_directory(
        self,
        directory: str,
        glob_patterns: Optional[List[str]] = None,
    ) -> List[Document]:
        """
        Load documents from a directory.

        Args:
            directory: Path to directory containing documents
            glob_patterns: List of glob patterns to match files (e.g., ["**/*.md", "**/*.txt"])

        Returns:
            List of loaded documents
        """
        if glob_patterns is None:
            glob_patterns = ["**/*.md", "**/*.txt", "**/*.py"]

        all_docs = []

        for pattern in glob_patterns:
            try:
                if pattern.endswith(".md"):
                    loader = DirectoryLoader(
                        directory,
                        glob=pattern,
                        loader_cls=UnstructuredMarkdownLoader,
                        show_progress=True,
                    )
                else:
                    loader = DirectoryLoader(
                        directory,
                        glob=pattern,
                        loader_cls=TextLoader,
                        show_progress=True,
                    )

                docs = loader.load()
                all_docs.extend(docs)
                logger.info(f"Loaded {len(docs)} documents matching {pattern}")

            except Exception as e:
                logger.warning(f"Error loading documents with pattern {pattern}: {e}")

        return all_docs

    def load_documents_from_files(self, file_paths: List[str]) -> List[Document]:
        """
        Load documents from specific file paths.

        Args:
            file_paths: List of file paths to load

        Returns:
            List of loaded documents
        """
        docs = []

        for file_path in file_paths:
            try:
                if file_path.endswith(".md"):
                    loader = UnstructuredMarkdownLoader(file_path)
                else:
                    loader = TextLoader(file_path)

                doc = loader.load()
                docs.extend(doc)
                logger.info(f"Loaded document: {file_path}")

            except Exception as e:
                logger.warning(f"Error loading document {file_path}: {e}")

        return docs

    def add_documents_from_text(self, texts: List[str], metadatas: Optional[List[Dict]] = None) -> List[Document]:
        """
        Create documents from raw text.

        Args:
            texts: List of text strings
            metadatas: Optional list of metadata dicts for each text

        Returns:
            List of documents
        """
        docs = []
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            doc = Document(page_content=text, metadata=metadata)
            docs.append(doc)

        return docs

    def index_documents(self, documents: List[Document]):
        """
        Index documents into the vector database.

        Args:
            documents: List of documents to index
        """
        if not documents:
            logger.warning("No documents to index")
            return

        # Split documents into chunks
        split_docs = self.text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} documents into {len(split_docs)} chunks")

        # Create or update vector store
        if self.vectorstore is None:
            self.vectorstore = Chroma.from_documents(
                documents=split_docs,
                embedding=self.embeddings,
                collection_name=self.collection_name,
                persist_directory=self.persist_directory,
            )
        else:
            self.vectorstore.add_documents(split_docs)

        logger.info(f"Indexed {len(split_docs)} document chunks")

    def load_existing_index(self):
        """Load an existing vector database index."""
        if os.path.exists(self.persist_directory):
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory,
            )
            logger.info("Loaded existing vector database index")
        else:
            logger.warning(f"No existing index found at {self.persist_directory}")

    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict] = None,
    ) -> List[Document]:
        """
        Search for relevant documents.

        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Optional metadata filter

        Returns:
            List of relevant documents
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Index documents first.")

        if filter_dict:
            results = self.vectorstore.similarity_search(
                query, k=k, filter=filter_dict
            )
        else:
            results = self.vectorstore.similarity_search(query, k=k)

        return results

    def search_with_scores(
        self,
        query: str,
        k: int = 5,
    ) -> List[tuple[Document, float]]:
        """
        Search for relevant documents with relevance scores.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of (document, score) tuples
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Index documents first.")

        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return results

    def format_search_results(self, documents: List[Document]) -> str:
        """
        Format search results as a string for context.

        Args:
            documents: List of documents

        Returns:
            Formatted string
        """
        if not documents:
            return "No relevant information found."

        formatted = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "Unknown")
            content = doc.page_content.strip()
            formatted.append(f"[Source {i}: {source}]\n{content}\n")

        return "\n".join(formatted)

    def get_context_for_query(self, query: str, k: int = 5) -> str:
        """
        Get formatted context for a query.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            Formatted context string
        """
        docs = self.search(query, k=k)
        return self.format_search_results(docs)

    def clear_index(self):
        """Clear the vector database index."""
        if self.vectorstore is not None:
            self.vectorstore.delete_collection()
            self.vectorstore = None
            logger.info("Cleared vector database index")


def build_knowledge_base(
    source_paths: List[str],
    persist_directory: str = "./chroma_db",
    collection_name: str = "product_knowledge",
    is_directory: bool = True,
    glob_patterns: Optional[List[str]] = None,
    anthropic_api_key: Optional[str] = None,
) -> KnowledgeBase:
    """
    Build a knowledge base from source documents.

    Args:
        source_paths: List of paths to directories or files
        persist_directory: Directory to persist the vector database
        collection_name: Name of the collection
        is_directory: Whether source_paths are directories or files
        glob_patterns: Glob patterns for directory loading
        anthropic_api_key: API key for Anthropic

    Returns:
        Initialized KnowledgeBase instance
    """
    kb = KnowledgeBase(
        persist_directory=persist_directory,
        collection_name=collection_name,
        anthropic_api_key=anthropic_api_key,
    )

    all_docs = []

    for path in source_paths:
        if is_directory:
            docs = kb.load_documents_from_directory(path, glob_patterns)
        else:
            docs = kb.load_documents_from_files([path])

        all_docs.extend(docs)

    if all_docs:
        kb.index_documents(all_docs)
        logger.info(f"Built knowledge base with {len(all_docs)} documents")
    else:
        logger.warning("No documents loaded into knowledge base")

    return kb
