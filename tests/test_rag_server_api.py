import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Mock the vectorstore loading before importing the app
with patch('wiki_rag.rag_server_api.load_vectorstore') as mock_load:
    mock_load.return_value = MagicMock()
    from wiki_rag.rag_server_api import app


class TestRagServerAPI:
    def setup_method(self):
        self.client = TestClient(app)
        # Generate test encryption key
        self.test_key = AESGCM.generate_key(bit_length=256)
        self.test_key_base64 = base64.b64encode(self.test_key).decode()
    
    def test_test_endpoint(self):
        # The /test endpoint is POST and expects a Query object
        # It returns the vectorstore object in results
        response = self.client.post("/test", json={"query": "test query"})
        assert response.status_code == 200
        # The test endpoint returns the vectorstore in results
        assert "results" in response.json()
    
    @patch('wiki_rag.rag_server_api.load_vectorstore')
    def test_rag_endpoint_plaintext(self, mock_load_vectorstore):
        # Mock the vectorstore
        mock_doc = MagicMock()
        mock_doc.page_content = "Python is a programming language."
        mock_doc.metadata = {"source": "wikipedia", "title": "Python"}
        
        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search.return_value = [mock_doc]
        mock_load_vectorstore.return_value = mock_vectorstore
        
        # Test plaintext query
        response = self.client.post(
            "/rag",
            json={"query": "What is Python?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["results"][0]["content"] == "Python is a programming language."
        assert data["results"][0]["metadata"]["title"] == "Python"
    
    @patch('wiki_rag.rag_server_api.do_encryption', True)
    @patch('wiki_rag.rag_server_api.aes_key_base64')
    @patch('wiki_rag.rag_server_api.load_vectorstore')
    def test_rag_endpoint_encrypted(self, mock_load_vectorstore, mock_aes_key):
        # Set up encryption key
        mock_aes_key.__str__.return_value = self.test_key_base64
        
        # Mock the vectorstore
        mock_doc = MagicMock()
        mock_doc.page_content = "Java is a programming language."
        mock_doc.metadata = {"source": "wikipedia", "title": "Java"}
        
        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search.return_value = [mock_doc]
        mock_load_vectorstore.return_value = mock_vectorstore
        
        # Import after patching to get the encrypted version
        from wiki_rag.rag_server_api import encrypt_message
        
        # Encrypt the query
        query = "What is Java?"
        encrypted_query = encrypt_message(query, self.test_key_base64)
        
        # Test encrypted query
        response = self.client.post(
            "/rag",
            json={"query": encrypted_query}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Response should be encrypted
        assert "encrypted_results" in data
        
        # Decrypt and verify response
        from wiki_rag.rag_server_api import decrypt_message
        decrypted_results = decrypt_message(data["encrypted_results"], self.test_key_base64)
        
        # Parse the decrypted JSON
        import json
        results = json.loads(decrypted_results)
        assert results["results"][0]["content"] == "Java is a programming language."
    
    @patch('wiki_rag.rag_server_api.load_vectorstore')
    def test_rag_endpoint_with_k_parameter(self, mock_load_vectorstore):
        # Mock multiple documents
        docs = []
        for i in range(5):
            mock_doc = MagicMock()
            mock_doc.page_content = f"Document {i}"
            mock_doc.metadata = {"title": f"Title {i}"}
            docs.append(mock_doc)
        
        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search.return_value = docs[:3]  # Return first 3
        mock_load_vectorstore.return_value = mock_vectorstore
        
        # Test with k=3
        response = self.client.post(
            "/rag",
            json={"query": "test query", "k": 3}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3
        
        # Verify similarity_search was called with k=3
        mock_vectorstore.similarity_search.assert_called_with("test query", k=3)
    
    @patch('wiki_rag.rag_server_api.load_vectorstore')
    def test_rag_endpoint_empty_results(self, mock_load_vectorstore):
        # Mock empty results
        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search.return_value = []
        mock_load_vectorstore.return_value = mock_vectorstore
        
        response = self.client.post(
            "/rag",
            json={"query": "nonexistent topic"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
    
    def test_rag_endpoint_missing_query(self):
        response = self.client.post(
            "/rag",
            json={}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_provision_endpoint(self):
        # Test key provisioning
        test_key = "test_aes_key_base64_encoded_string"
        
        response = self.client.post(
            "/provision",
            json={"aes_key": test_key}
        )
        
        assert response.status_code == 200
        assert response.json() == {"status": "Key provisioned successfully"}
    
    def test_provision_endpoint_missing_key(self):
        response = self.client.post(
            "/provision",
            json={}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
        # Verify validation error details
        assert "aes_key" in str(response.json())
    
    @patch('wiki_rag.rag_server_api.load_vectorstore')
    def test_vectorstore_loading_once(self, mock_load_vectorstore):
        # Ensure vectorstore is loaded only once (singleton pattern)
        mock_vectorstore = MagicMock()
        mock_load_vectorstore.return_value = mock_vectorstore
        
        # Make multiple requests
        for _ in range(3):
            response = self.client.post(
                "/rag",
                json={"query": "test"}
            )
            assert response.status_code == 200
        
        # Vectorstore should be loaded only once
        mock_load_vectorstore.assert_called_once()