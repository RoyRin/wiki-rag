import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import torch
import numpy as np
from wiki_rag.rag import (
    batched,
    ModelEmbeddings,
    PromptedBGE,
    download_and_build_rag_from_huggingface
)


class TestRag:
    def test_batched(self):
        # Test basic batching
        items = list(range(10))
        batches = list(batched(items, 3))
        
        assert len(batches) == 4
        assert batches[0] == [0, 1, 2]
        assert batches[1] == [3, 4, 5]
        assert batches[2] == [6, 7, 8]
        assert batches[3] == [9]
        
        # Test exact division
        items = list(range(9))
        batches = list(batched(items, 3))
        assert len(batches) == 3
        assert all(len(batch) == 3 for batch in batches)
        
        # Test single batch
        items = [1, 2]
        batches = list(batched(items, 5))
        assert len(batches) == 1
        assert batches[0] == [1, 2]
        
        # Test empty iterable
        batches = list(batched([], 3))
        assert len(batches) == 0
    
    def test_model_embeddings_initialization(self):
        # ModelEmbeddings expects model, tokenizer, and device to be passed in
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        
        # Create ModelEmbeddings instance with required parameters
        embeddings = ModelEmbeddings(model=mock_model, tokenizer=mock_tokenizer, device='cpu')
        
        # Verify attributes were set correctly
        assert embeddings.model == mock_model
        assert embeddings.tokenizer == mock_tokenizer
        assert embeddings.device == 'cpu'
    
    def test_model_embeddings_embed_documents(self):
        # Setup mocks
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        
        # Create mock tensor objects that have the .to() method
        mock_input_ids = MagicMock()
        mock_input_ids.to = MagicMock(return_value=torch.tensor([[1, 2, 3], [4, 5, 6]]))
        
        mock_attention_mask = MagicMock()
        mock_attention_mask.to = MagicMock(return_value=torch.tensor([[1, 1, 1], [1, 1, 0]]))
        
        # Mock tokenizer to return an object with .to() method
        mock_tokenizer_output = MagicMock()
        mock_tokenizer_output.to = MagicMock(return_value={
            'input_ids': torch.tensor([[1, 2, 3], [4, 5, 6]]),
            'attention_mask': torch.tensor([[1, 1, 1], [1, 1, 0]])
        })
        mock_tokenizer.return_value = mock_tokenizer_output
        
        # Mock model output
        mock_output = MagicMock()
        mock_output.hidden_states = (torch.randn(2, 3, 768),)  # batch_size=2, seq_len=3, hidden_dim=768
        mock_model.return_value = mock_output
        
        embeddings = ModelEmbeddings(model=mock_model, tokenizer=mock_tokenizer, device='cpu')
        
        # Test embedding documents
        texts = ["Document 1", "Document 2"]
        result = embeddings.embed_documents(texts)
        
        assert len(result) == 2
        assert all(isinstance(emb, list) for emb in result)
        assert all(len(emb) == 768 for emb in result)  # Check embedding dimension
    
    def test_prompted_bge_initialization(self):
        # PromptedBGE inherits from HuggingFaceEmbeddings
        with patch('wiki_rag.rag.HuggingFaceEmbeddings.__init__') as mock_init:
            mock_init.return_value = None
            
            # PromptedBGE uses default model_name if not specified
            prompted_bge = PromptedBGE()
            
            # Check that parent class was initialized
            mock_init.assert_called_once()
    
    def test_prompted_bge_embed_documents(self):
        # Create a PromptedBGE instance and mock the parent's embed_documents
        with patch('langchain_community.embeddings.HuggingFaceEmbeddings.embed_documents') as mock_embed:
            mock_embed.return_value = [[0.1, 0.2], [0.3, 0.4]]
            
            prompted_bge = PromptedBGE()
            
            texts = ["Document 1", "Document 2"]
            result = prompted_bge.embed_documents(texts)
            
            # Check that prompts were added
            expected_texts = [
                "Represent this sentence for searching relevant passages: Document 1",
                "Represent this sentence for searching relevant passages: Document 2"
            ]
            mock_embed.assert_called_once_with(expected_texts)
            
            assert result == [[0.1, 0.2], [0.3, 0.4]]
    
    def test_prompted_bge_embed_query(self):
        # Create a PromptedBGE instance and mock the parent's embed_query
        with patch('langchain_community.embeddings.HuggingFaceEmbeddings.embed_query') as mock_embed:
            mock_embed.return_value = [0.5, 0.6]
            
            prompted_bge = PromptedBGE()
            
            query = "What is Python?"
            result = prompted_bge.embed_query(query)
            
            # Check that query prompt was added
            expected_query = "Represent this sentence for searching relevant passages: What is Python?"
            mock_embed.assert_called_once_with(expected_query)
            
            assert result == [0.5, 0.6]
    
    @patch('wiki_rag.rag.os.path.exists')
    @patch('wiki_rag.rag.FAISS.load_local')
    def test_download_and_build_rag_existing_index(self, mock_faiss_load, mock_exists):
        # Test when index already exists
        mock_exists.return_value = True
        mock_vectorstore = MagicMock()
        mock_faiss_load.return_value = mock_vectorstore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # The function uses default parameters if not provided
            result = download_and_build_rag_from_huggingface()
            
            # Should check for existing index
            mock_exists.assert_called()
            # Should load existing index
            mock_faiss_load.assert_called_once()
            assert result == mock_vectorstore
    
    @patch('wiki_rag.rag.snapshot_download')
    @patch('wiki_rag.rag.os.path.exists')
    @patch('wiki_rag.rag.FAISS.load_local')
    def test_download_and_build_rag_download_index(self, mock_faiss_load, mock_exists, mock_snapshot):
        # Test when index needs to be downloaded
        mock_exists.return_value = False
        mock_vectorstore = MagicMock()
        mock_faiss_load.return_value = mock_vectorstore
        mock_snapshot.return_value = "/path/to/downloaded"
        
        result = download_and_build_rag_from_huggingface()
        
        # Should download from HuggingFace
        mock_snapshot.assert_called_once()
        
        # Should load the downloaded index
        mock_faiss_load.assert_called_once()
        assert result == mock_vectorstore