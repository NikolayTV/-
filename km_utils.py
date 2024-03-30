import asyncio
from datetime import datetime, timedelta
import google.generativeai as genai
import re, os, json
import aiofiles
import google



async def save_description_to_file(description, path):
    if description is not None:
        async with aiofiles.open(path, 'w') as file:
            await file.write(description)



def create_folder_structure(base_path, coap_json):
    """
    creates folders and write articels to content.txt
    """
    for section in coap_json.keys():
        section_path = os.path.join(base_path, section)
        os.makedirs(section_path, exist_ok=True)
        print(f'Created section folder: {section_path}')

        for chapter in coap_json[section]:
            chapter_path = os.path.join(section_path, chapter)
            os.makedirs(chapter_path, exist_ok=True)
            print(f'Created chapter folder: {chapter_path}')

            for article in coap_json[section][chapter]:
                article_path = os.path.join(chapter_path, article)
                os.makedirs(article_path, exist_ok=True)
                print(f'Created article folder: {article_path}')

                article_txt_path = os.path.join(article_path, 'content.txt')
                with open(article_txt_path, 'w') as file: file.write(coap_json[section][chapter][article])
                print(f'Created file: {article_txt_path}')


def read_text_file_if_exists(path):
    """
    Reads and returns the content of a text file if it exists; returns None otherwise.
    """
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()
    return None



def create_nested_json(text):
    """
    Создаёт вложенную структуру JSON из предоставленного текста книги, где заголовки разделов,
    глав и статей являются ключами, а текст на последнем уровне - значениями.
    """

    # Измененные регулярные выражения, чтобы захватывать весь заголовок целиком
    section_pattern = r"(Раздел\s+.+)"
    chapter_pattern = r"(Глава\s+.+)"
    article_pattern = r"(Статья\s+.+)"
    
    json_data = {}
    current_section = None
    current_chapter = None
    current_article = None

    for line in text.splitlines():
        line = line.strip()

        # Изменения применены ниже для сохранения полных заголовков
        section_match = re.match(section_pattern, line)
        if section_match:
            section_title = section_match.group(0)  # Изменено для захвата всей строки
            json_data[section_title] = {}
            current_section = section_title
            current_chapter = None
            current_article = None
            continue

        chapter_match = re.match(chapter_pattern, line)
        if chapter_match and current_section is not None:
            chapter_title = chapter_match.group(0)  # Изменено для захвата всей строки
            json_data[current_section][chapter_title] = {}
            current_chapter = chapter_title
            current_article = None
            continue

        article_match = re.match(article_pattern, line)
        if article_match and current_section is not None and current_chapter is not None:
            article_title = article_match.group(0)  # Изменено для захвата всей строки
            current_article = article_title[:250] # ограничим название статей до 250 символов - максимальная длина папки в макбуке
            if current_article not in json_data[current_section][current_chapter]:
                json_data[current_section][current_chapter][current_article] = ""
            continue

        if current_article:
            json_data[current_section][current_chapter][current_article] += (line.strip() + "\n")

    return json_data



def dir_to_json_with_txt_content(path):
    """
    Recursively walks through a directory path, creating a nested dictionary structure that mirrors the
    directory structure. Specifically looks for 'description.txt' and 'description_short.txt' files to
    include their content if they exist.
    """
    structure = {"childs": {}}  # Initialize the current item's structure

    # Check if files exist and add to dict
    for filename in ['description', 'short_description', 'content']:
        if os.path.exists(os.path.join(path, f'{filename}.txt')):
            structure[f'{filename}'] = read_text_file_if_exists(os.path.join(path, f'{filename}.txt'))


    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            # Recursively process subdirectories and include their structures in the childs key
            structure['childs'][item] = dir_to_json_with_txt_content(item_path)

    # If 'childs' is empty, remove it from the structure
    if not structure['childs']:
        del structure['childs']
    
    return structure

def get_ToCs(base_path = 'coap_map'):
    nested_json = dir_to_json_with_txt_content(base_path)

    ToC_sections = {}
    for section in nested_json['childs'].keys():
        ToC_sections[section] = nested_json['childs'][section]['description']

    ToC_chapters = {}
    for section in nested_json['childs'].keys():
        ToC_chapters[section] = {}
        for chapter in nested_json['childs'][section]['childs'].keys():
            ToC_chapters[section][chapter] = "; ".join(nested_json['childs'][section]['childs'][chapter]['childs'].keys())
            # ToC_chapters[section][chapter] = nested_json['childs'][section]['childs'][chapter]['description']

    ToC_articles_short_descriptions = {}
    for section in nested_json['childs'].keys():
        ToC_articles_short_descriptions[section] = {}
        for chapter in nested_json['childs'][section]['childs'].keys():
            ToC_articles_short_descriptions[section][chapter] = {}
            for article in nested_json['childs'][section]['childs'][chapter]['childs'].keys():
                ToC_articles_short_descriptions[section][chapter][article] = nested_json['childs'][section]['childs'][chapter]['childs'][article]['short_description']

    ToC_articles_descriptions = {}
    for section in nested_json['childs'].keys():
        ToC_articles_descriptions[section] = {}
        for chapter in nested_json['childs'][section]['childs'].keys():
            ToC_articles_descriptions[section][chapter] = {}
            for article in nested_json['childs'][section]['childs'][chapter]['childs'].keys():
                ToC_articles_descriptions[section][chapter][article] = nested_json['childs'][section]['childs'][chapter]['childs'][article]['description']

    return {'ToC_sections':ToC_sections, 'ToC_chapters':ToC_chapters, 'ToC_articles_short_descriptions':ToC_articles_short_descriptions,
            'ToC_articles_descriptions':ToC_articles_descriptions}