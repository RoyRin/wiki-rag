from pathlib import Path
import json
import os
import glob
from xml.etree import ElementTree as ET
import re
from tqdm import tqdm
import pandas as pd
import json
import pickle


def save_json(d, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=4)


def save_pickle(d, filepath):
    with open(filepath, 'wb') as f:
        pickle.dump(d, f)


def get_title_to_path_index(json_dir, title_to_file_path_f_pkl):
    """extract dictionary that maps {title: (path , line-number )}
    assumes that the data is contained in the wiki-extractor json format,

        ├── AA
        │   ├── wiki_00
        │   ├── wiki_01
            ...
        └── AB
            ├── wiki_00
            ├── wiki_01
            ...
        where `wiki_*` is a file where each line is a JSON.dumps dictionary for a wikipedia article
    Args:
        json_dir (_type_): path to wikipedia in json format
        title_to_file_path_f_pkl (_type_): where to save the {title: (file-path, line-number)} dict

    Returns:
        title_to_file_path
    """
    jsons_ = list(json_dir.glob('**/wiki_*'))
    title_to_file_path = {}

    if title_to_file_path_f_pkl.exists():
        with open(title_to_file_path_f_pkl, 'rb') as f:
            title_to_file_path = pickle.load(f)

    else:
        for path in tqdm(jsons_):
            with open(path, 'r', encoding='utf-8') as f:
                for line_number, line in enumerate(f, start=1):
                    try:
                        data = json.loads(line)
                        title = data['title']
                        title = clean_title(title)
                        # Save both file path and line number
                        title_to_file_path[title] = (str(path), line_number)
                    except json.JSONDecodeError:
                        continue
        print(f"saved json")
        save_pickle(title_to_file_path, title_to_file_path_f_pkl)
    return title_to_file_path


def read_line_from_file(path, line_number):
    """Read a specific line (1-indexed) from a text file."""
    with open(path, 'r', encoding='utf-8') as f:
        for current_line_number, line in enumerate(f, start=1):
            if current_line_number == line_number:
                return line
    raise ValueError(f"Line number {line_number} not found in file: {path}")


def get_wiki_page(title, title_to_file_path):
    path, row_num = title_to_file_path.get(title, (None, None))
    if path is None:
        return None
    # read the json file, and find the line with the title
    data = read_line_from_file(path, row_num)
    return json.loads(data)


def get_sorted_english_df(output_f, raw_stats_f=None):
    # Replace 'filename.txt' with your actual file path

    if not output_f.exists() and raw_stats_f is not None:
        """
        Example from stats file:
        project page_title views bytes
        ```
        en.m Fertile_material 1 0
        en.m Fertilisation 3 0
        en Fertiliser 1 0
        en.m Fertilisers_and_Chemicals_Travancore 1 0
        """
        df = pd.read_csv(raw_stats_f,
                         sep=' ',
                         header=None,
                         names=['project', 'page_title', 'views', 'bytes'])

        english_mask = (df["project"] == "en") | (df["project"] == "en.m")
        english_df = df[english_mask]

        english_df.head()

        english_df = english_df.groupby('page_title', as_index=False).agg({
            'views':
            'sum',
            'bytes':
            'sum'
        })

        # sort by views
        english_df = english_df.sort_values(by='views', ascending=False)
        # combine views from en and en.m

        # for page ttles swap _ wit " "
        english_df['page_title'] = english_df['page_title'].str.replace(
            '_', ' ')

        # drop bytes col
        english_df = english_df.drop(columns=['bytes'])
        # save to asset_dir
        english_df.to_csv(output_f, index=False)

        print(f"saved to {output_f}")
    else:
        english_df = pd.read_csv(output_f)
        print(f"loaded from {output_f}")
    return english_df


def clean_title(title):
    date_clean_title = re.sub(r'\s*\(\d{4}\)', '',
                              title)  # remove date at the end

    title = date_clean_title.replace(' ', '')
    # remove :
    title = title.replace(':', '')
    # title to lower
    title = title.replace("-", "")
    title = title.lower()
    return title


def extract_abstract_from_text(text):

    for paragraph in text.split('\n'):
        paragraph = paragraph.strip()
        if paragraph:
            return paragraph
    return ""


def read_article_from_json(full_path, offset):
    """ 
    Reads a single article from the JSON file at the given offset.
    """
    with open(full_path, 'r', encoding='utf-8') as f:
        f.seek(offset)
        line = f.readline()
        try:
            data = json.loads(line)
            title = data.get("title")
            text = data.get("text", "")
            return title, text
        except json.JSONDecodeError:
            return None, None


def wikipedia_abstract_generator(path_to_extracted_dir):
    """
    Generator function to yield (title, abstract) tuples from extracted Wikipedia JSON files.
    """
    for dirpath, _, filenames in os.walk(path_to_extracted_dir):
        for fname in sorted(filenames):
            full_path = os.path.join(dirpath, fname)
            with open(full_path, 'r', encoding='utf-8') as f:
                while True:
                    offset = f.tell()
                    line = f.readline()
                    if not line:
                        break
                    try:
                        # Try to decode to check validity before calling read_article
                        json.loads(line)  # lightweight check
                    except json.JSONDecodeError:
                        continue

                    title, text = read_article_from_json(full_path, offset)
                    if not title or not text:
                        continue
                    abstract = extract_abstract_from_text(text)
                    if abstract:
                        yield (title.strip(), abstract)


def build_title_index(path_to_extracted_dir):
    """ 
    Extracts a title index from the extracted Wikipedia JSON files. For fast look up.
    """
    index = {}
    for dirpath, _, filenames in os.walk(path_to_extracted_dir):
        for fname in sorted(filenames):
            full_path = os.path.join(dirpath, fname)
            with open(full_path, 'r', encoding='utf-8') as f:
                offset = 0
                while True:
                    line = f.readline()
                    if not line:
                        break
                    try:
                        data = json.loads(line)
                        title = data.get("title")
                        if title:
                            index[title] = (full_path, offset)
                    except json.JSONDecodeError:
                        pass
                    offset = f.tell()
    return index


def get_article_remote(title, abstract_only=False):
    import wikipedia
    # Set language (optional, default is English)
    wikipedia.set_lang("en")
    if abstract_only:
        # Get the summary (i.e., abstract / lead section)
        summary = wikipedia.summary(title)
        return summary

    # Get the full page content
    page = wikipedia.page(title)
    content = page.content
    return content


def parse_wikiextractor_output(extracted_dir):
    for file_path in glob.glob(os.path.join(extracted_dir, '**', 'wiki_*'),
                               recursive=True):
        with open(file_path, 'r', encoding='utf-8') as f:
            contents = f.read()
            docs = contents.split('</doc>')
            for doc in docs:
                doc = doc.strip()
                if not doc:
                    continue
                try:
                    doc += '</doc>'  # Add closing tag back
                    xml_doc = ET.fromstring(doc)
                    yield {
                        'id': xml_doc.attrib['id'],
                        'title': xml_doc.attrib['title'],
                        'url': xml_doc.attrib['url'],
                        'text': xml_doc.text.strip() if xml_doc.text else ''
                    }
                except Exception as e:
                    print(f"Skipping malformed doc: {e}")
