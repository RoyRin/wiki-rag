import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from wiki_rag.wikipedia import wikipedia_abstract_generator, get_title_to_path_index
from wiki_rag.rag import batched


@pytest.mark.integration
class TestIntegration:
    def test_wikipedia_abstract_generator_integration(self, mock_wikipedia_data, temp_dir):
        """Test the full pipeline of reading Wikipedia data and generating abstracts."""
        # Create page view data
        pageviews_file = temp_dir / "pageviews.csv"
        pageviews_file.write_text(
            "title,views\n"
            "Python_(programming_language),1000000\n"
            "Machine_learning,500000\n"
            "Natural_language_processing,300000\n"
        )
        
        # Test the generator - it only takes one parameter
        abstracts = list(wikipedia_abstract_generator(str(temp_dir)))
        
        assert len(abstracts) == 3
        
        # Check that we got abstracts (order may vary based on file system)
        titles = [title for title, _ in abstracts]
        assert "Python (programming language)" in titles
        assert "Machine learning" in titles
        assert "Natural language processing" in titles
        
        # Check that abstracts contain expected content
        assert "high-level" in abstracts[0][1]
        assert "artificial intelligence" in abstracts[1][1]
        assert "linguistics" in abstracts[2][1]
    
    def test_batched_processing_with_generator(self):
        """Test batched processing of a generator."""
        def number_generator(n):
            for i in range(n):
                yield i
        
        # Process in batches
        batches = list(batched(number_generator(25), 10))
        
        assert len(batches) == 3
        assert batches[0] == list(range(10))
        assert batches[1] == list(range(10, 20))
        assert batches[2] == list(range(20, 25))
    
    @patch('wiki_rag.rag.FAISS')
    @patch('wiki_rag.rag.PromptedBGE')
    def test_construct_faiss_integration(self, mock_embeddings_class, mock_faiss, mock_wikipedia_data, temp_dir):
        """Test the FAISS index construction process."""
        from wiki_rag.rag import construct_faiss
        
        # Mock embeddings
        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3]] * 10
        mock_embeddings_class.return_value = mock_embeddings
        
        # Mock FAISS
        mock_vectorstore = MagicMock()
        mock_faiss.from_documents.return_value = mock_vectorstore
        
        # Create page views file
        pageviews_file = temp_dir / "pageviews.csv"
        pageviews_file.write_text(
            "title,views\n"
            "Python_(programming_language),1000000\n"
        )
        
        # Run construction with correct parameters
        # construct_faiss expects: english_df, title_to_file_path, SAVE_PATH, embeddings, max_articles
        import pandas as pd
        english_df = pd.DataFrame({
            'page_title': ['Python (programming language)'],
            'views': [1000000]
        })
        title_to_file_path = {'python (programming language)': (str(mock_wikipedia_data), 1)}
        save_path = temp_dir / "faiss_index"
        
        construct_faiss(
            english_df=english_df,
            title_to_file_path=title_to_file_path,
            SAVE_PATH=str(save_path),
            embeddings=mock_embeddings,
            max_articles=1
        )
        
        # Verify FAISS was created with documents
        mock_faiss.from_documents.assert_called_once()
        call_args = mock_faiss.from_documents.call_args
        documents = call_args[0][0]
        
        assert len(documents) >= 1
        assert documents[0].metadata["title"] == "Python (programming language)"
    
    def test_title_index_and_retrieval(self, mock_wikipedia_data, temp_dir):
        """Test building title index and retrieving articles."""
        from wiki_rag.wikipedia import get_title_to_path_index, get_wiki_page
        
        # Build index
        index = get_title_to_path_index(temp_dir)
        
        # Test retrieval
        article = get_wiki_page("python (programming language)", index)
        assert article is not None
        assert article["title"] == "Python (programming language)"
        assert "high-level" in article["text"]
        
        # Test with cleaned title
        article = get_wiki_page("python programming language", index)
        assert article is not None
        assert article["title"] == "Python (programming language)"
        
        # Test non-existent article
        article = get_wiki_page("nonexistent article", index)
        assert article is None
    
    @patch('wiki_rag.rag_server_api.load_vectorstore')
    def test_server_api_full_flow(self, mock_load_vectorstore):
        """Test the full API server flow from query to response."""
        from fastapi.testclient import TestClient
        from wiki_rag.rag_server_api import app
        
        # Mock vectorstore with realistic data
        mock_doc1 = MagicMock()
        mock_doc1.page_content = "Python is a versatile programming language used for web development, data science, and automation."
        mock_doc1.metadata = {"title": "Python (programming language)", "source": "wikipedia"}
        
        mock_doc2 = MagicMock()
        mock_doc2.page_content = "Machine learning enables computers to learn from data without explicit programming."
        mock_doc2.metadata = {"title": "Machine learning", "source": "wikipedia"}
        
        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search.return_value = [mock_doc1, mock_doc2]
        mock_load_vectorstore.return_value = mock_vectorstore
        
        client = TestClient(app)
        
        # Test query
        response = client.post(
            "/rag",
            json={"query": "What is Python used for?", "k": 2}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) == 2
        assert data["results"][0]["metadata"]["title"] == "Python (programming language)"
        assert "versatile" in data["results"][0]["content"]