import pytest
import tempfile
import json
from pathlib import Path
from wiki_rag.wikipedia import (
    clean_title,
    get_title_to_path_index,
    get_wiki_page,
    extract_abstract_from_text,
    parse_wikiextractor_output
)


class TestWikipedia:
    def test_clean_title(self):
        assert clean_title("Example_Article") == "example_article"
        assert clean_title("Test (2023)") == "test"
        assert clean_title("Article with spaces") == "articlewithspaces"
        assert clean_title("Special:Characters") == "specialcharacters"
        assert clean_title("Date (2023)") == "date"
        assert clean_title("") == ""
        assert clean_title("Dash-Test") == "dashtest"
    
    def test_extract_abstract_from_text(self):
        text = """First paragraph is the abstract.
        
        Second paragraph should not be included.
        
        Third paragraph also not included."""
        
        assert extract_abstract_from_text(text) == "First paragraph is the abstract."
        
        text_with_single_line = "Only one line here."
        assert extract_abstract_from_text(text_with_single_line) == "Only one line here."
        
        empty_text = ""
        assert extract_abstract_from_text(empty_text) == ""
        
        text_with_empty_first = """
        
        Second line is actually first."""
        assert extract_abstract_from_text(text_with_empty_first) == "Second line is actually first."
    
    def test_get_title_to_path_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create test Wikipedia JSON files in wiki-extractor format
            subdir = tmppath / "AA"
            subdir.mkdir()
            wiki_file1 = subdir / "wiki_00"
            wiki_file2 = subdir / "wiki_01"
            
            articles1 = [
                {"id": "1", "url": "https://en.wikipedia.org/wiki/Python", "title": "Python", "text": "Python is a programming language."},
                {"id": "2", "url": "https://en.wikipedia.org/wiki/Java", "title": "Java", "text": "Java is also a programming language."}
            ]
            
            articles2 = [
                {"id": "3", "url": "https://en.wikipedia.org/wiki/C++", "title": "C++", "text": "C++ is a compiled language."}
            ]
            
            with open(wiki_file1, 'w') as f:
                for article in articles1:
                    f.write(json.dumps(article) + '\n')
            
            with open(wiki_file2, 'w') as f:
                for article in articles2:
                    f.write(json.dumps(article) + '\n')
            
            # Test index creation
            pkl_file = tmppath / "index.pkl"
            index = get_title_to_path_index(tmppath, pkl_file)
            
            assert "python" in index
            assert "java" in index
            assert "c++" in index
            
            # Verify file paths and line numbers
            assert index["python"][0] == str(wiki_file1)
            assert index["java"][0] == str(wiki_file1)
            assert index["c++"][0] == str(wiki_file2)
            
            # Line numbers should be different for different articles
            assert index["python"][1] == 1  # First line
            assert index["java"][1] == 2  # Second line
            assert index["c++"][1] == 1  # First line in second file
    
    def test_get_wiki_page(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create wiki-extractor format
            subdir = tmppath / "AA"
            subdir.mkdir()
            wiki_file = subdir / "wiki_00"
            article = {"id": "1", "url": "https://en.wikipedia.org/wiki/Test", "title": "Test Article", "text": "This is a test article."}
            
            with open(wiki_file, 'w') as f:
                f.write(json.dumps(article) + '\n')
            
            pkl_file = tmppath / "index.pkl"
            index = get_title_to_path_index(tmppath, pkl_file)
            
            # Test successful retrieval
            result = get_wiki_page("testarticle", index)  # clean_title removes spaces
            assert result["title"] == "Test Article"
            assert result["text"] == "This is a test article."
            
            # Test missing article
            result = get_wiki_page("nonexistent", index)
            assert result is None
    
    def test_parse_wikiextractor_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a wiki file with XML content
            wiki_file = Path(tmpdir) / "wiki_00"
            xml_content = '''<doc id="1" url="https://en.wikipedia.org/wiki/Test" title="Test Article">
Test content here.

More content.
</doc>

<doc id="2" url="https://en.wikipedia.org/wiki/Second" title="Second Article">
Second article content.
</doc>'''
            
            wiki_file.write_text(xml_content)
            
            articles = list(parse_wikiextractor_output(tmpdir))
            
            assert len(articles) == 2
            
            assert articles[0]["id"] == "1"
            assert articles[0]["title"] == "Test Article"
            assert articles[0]["url"] == "https://en.wikipedia.org/wiki/Test"
            assert articles[0]["text"] == "Test content here.\n\nMore content."
            
            assert articles[1]["id"] == "2"
            assert articles[1]["title"] == "Second Article"
            assert articles[1]["text"] == "Second article content."
            
            # Test empty directory
            empty_dir = Path(tmpdir) / "empty"
            empty_dir.mkdir()
            empty_articles = list(parse_wikiextractor_output(str(empty_dir)))
            assert len(empty_articles) == 0
            
            # Test malformed XML (should handle gracefully)
            bad_file = Path(tmpdir) / "wiki_bad"
            bad_file.write_text('''<doc id="3" title="Broken">
            Content without closing tag''')
            # Should not crash, just skip malformed docs
            articles = list(parse_wikiextractor_output(tmpdir))
            assert len(articles) == 2  # Only the 2 good docs from wiki_00