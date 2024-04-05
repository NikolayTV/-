import asyncio
from datetime import datetime, timedelta
import google.generativeai as genai
import re, os, json
import aiofiles
import google


def get_content_from_articles_response(ToC_articles, choosed_articles_responses):
    chapter_article_map = ''
    for choosed_articles_response in choosed_articles_responses[:]: 
        chapter_article_map += f"\n{choosed_articles_response.get('text_response')}"
    print('chapter_article_map:', chapter_article_map)


    ### TODO если статья больше 25к символов, то нужно использовать ее перефраз вместо контента
    
    results = []
    pattern = re.compile(r'Статья\s+\d+(\.\d+)*(-\d+)?\.')

    for one_path in chapter_article_map.split('\n'):
        match = pattern.search(one_path.strip())
        if match:
            article_id = match.group().strip()
            print(article_id)
            # Search for the full path to our article
            for section in ToC_articles.keys():
                for chapter in ToC_articles[section].keys():
                    # for article_title_id in ToC_articles[section][chapter].keys():
                    if article_id in ToC_articles[section][chapter].keys():
                        article_title = ToC_articles[section][chapter][article_id]['article_title']
                        content = ToC_articles[section][chapter][article_id]['article_content']
                        results.append({'article_id': article_id, 
                                        'article_title': article_title, 
                                        'content': content})

    # Remove duplicates based on article title
    unique_articles = {article['article_title']: article for article in results}.values()

    return list(unique_articles)


def split_list_by_size(input_list, size_limit=30000, max_item_size=25000):
    """
    Splits a list of strings (or other objects that can be converted to strings)
    into multiple lists, each as a string equivalent not exceeding size_limit characters.
    """
    parts = []  # List to hold the resulting lists of values
    current_part = []  # Current list part being filled
    current_size = 2  # Account for the empty list brackets '[]'

    for item in input_list:
        # Convert the item to string and calculate its size
        item_str = str(item)[:max_item_size]
        item_size = len(item_str)

        # Check if adding the current item would exceed the size limit
        if current_size + item_size + len(current_part) > size_limit:
            # If adding the item exceeds the size limit, append the current part to parts
            # and start a new part with the current item
            parts.append(current_part)
            current_part = [item_str]
            current_size = 2 + item_size  # Reset size for the new part, including brackets
        else:
            # If the item doesn't exceed the limit, add it to the current part
            current_part.append(item_str)
            current_size += item_size

    # After processing all items, add the final part if it's not empty
    if current_part:
        parts.append(current_part)

    return parts




def split_dict_by_size(input_dict, size_limit=30000):
    """
    Splits a dictionary into multiple dictionaries, each as in a string equivalent not exceeding size_limit characters.
    """
    parts = []  # List to hold the resulting dictionaries
    current_part = {}  # Current dictionary part being filled
    current_size = 2  # Account for the empty dictionary braces '{}'


    for key, value in input_dict.items():
        # Estimate size of current item. Add 4 for ': ' and ', ' (the latter for all but the last item)
        item_size = len(repr(key)) + len(repr(value)) + 4
        if current_size + item_size > size_limit:
            # Add the current part to the list and start a new one
            parts.append(current_part)
            current_part = {key: value}
            current_size = 2 + item_size  # Reset size for the new part, including braces
        else:
            # Add item to the current part
            current_part[key] = value
            current_size += item_size

    # Add the final part if not empty
    if current_part:
        parts.append(current_part)

    return parts


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
            current_article = article_title[:230] # ограничим название статей до 240 символов - максимальная длина папки в макбуке
            if current_article not in json_data[current_section][current_chapter]:
                json_data[current_section][current_chapter][current_article] = ""
            continue

        if current_article:
            json_data[current_section][current_chapter][current_article] += (line.strip() + "\n")

    return json_data


def clean_dict_from_corrupt_spaces(d):
    if isinstance(d, dict):
        return {clean_dict_from_corrupt_spaces(k): clean_dict_from_corrupt_spaces(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [clean_dict_from_corrupt_spaces(item) for item in d]
    elif isinstance(d, str):
        return d.replace('\xa0', ' ')
    else:
        return d
    
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
    
    structure = clean_dict_from_corrupt_spaces(structure)

    return structure


import re

def get_ToCs(base_path='coap_map'):
    # Получение структурированных данных из директории
    doc = dir_to_json_with_txt_content(base_path)

    # Инициализация структур данных для хранения информации
    ToC_sections = {}
    ToC_chapters = {}
    ToC_chapters_with_article_short_descriptions = {}
    ToC_articles = {}
    ToC_articles_short_descriptions = {}
    ToC_articles_descriptions = {}
    ToC_sections_articles_shortDescription = {}

    # Регулярное выражение для идентификации номера статьи
    pattern = re.compile(r'Статья\s+\d+(\.\d+)*(-\d+)?\.')

    for section, section_content in doc['childs'].items():
        section_description = section_content['description']
        ToC_sections[section] = section_description
        ToC_chapters[section] = {}
        ToC_chapters_with_article_short_descriptions[section] = {}
        ToC_articles[section] = {}
        ToC_articles_short_descriptions[section] = {}
        ToC_articles_descriptions[section] = {}
        ToC_sections_articles_shortDescription[section] = {}

        for chapter, chapter_content in section_content['childs'].items():
            chapter_articles = chapter_content['childs']
            chapter_article_names = "; ".join(chapter_articles.keys())
            ToC_chapters[section][chapter] = chapter_article_names
            ToC_chapters_with_article_short_descriptions[section][chapter] = {}
            ToC_articles[section][chapter] = {}
            ToC_articles_short_descriptions[section][chapter] = {}
            ToC_articles_descriptions[section][chapter] = {}

            for article_title, article_content in chapter_articles.items():
                if 'Утратила силу' in article_title or 'Не применяется с' in article_title:
                    continue
                
                match = pattern.search(article_title)
                article_id = match.group() if match else article_title

                article_short_description = article_content.get('short_description', '')
                article_full_content = article_content.get('content', '')
                article_description = article_content.get('description', '')

                ToC_chapters_with_article_short_descriptions[section][chapter][article_id] = article_short_description
                ToC_articles[section][chapter][article_id] = {'article_title':article_title, "article_content":article_full_content}
                ToC_articles_short_descriptions[section][chapter][article_id] = article_short_description
                ToC_articles_descriptions[section][chapter][article_id] = article_description
                ToC_sections_articles_shortDescription[section][article_id] = article_short_description

 
    # Сборка итогового словаря с информацией
    result = {
        'doc_with_childs': doc,
        'ToC_sections': ToC_sections,
        'ToC_chapters': ToC_chapters,
        'ToC_chapters_with_article_short_descriptions': ToC_chapters_with_article_short_descriptions,
        'ToC_articles': ToC_articles,
        'ToC_articles_short_descriptions': ToC_articles_short_descriptions,
        'ToC_articles_descriptions': ToC_articles_descriptions,
        'ToC_sections_articles_shortDescription': ToC_sections_articles_shortDescription
    }

    return result
