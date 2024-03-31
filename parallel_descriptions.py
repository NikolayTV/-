import asyncio, aiofiles
from datetime import datetime, timedelta
import google.generativeai as genai
from anthropic import AsyncAnthropic
import re, os, json
import google
from km_utils import dir_to_json_with_txt_content, save_description_to_file, create_nested_json, read_text_file_if_exists, create_folder_structure
from llm_api_calls import send_message_to_gemini_async


class RateLimiter:
    def __init__(self, calls_per_period, period=1.0):
        self.calls_per_period = calls_per_period
        self.period = timedelta(seconds=period)
        self.calls = []

    async def wait(self):
        now = datetime.now()
        
        while self.calls and now - self.calls[0] > self.period:
            self.calls.pop(0)
            
        if len(self.calls) >= self.calls_per_period:
            sleep_time = (self.period - (now - self.calls[0])).total_seconds()
            await asyncio.sleep(sleep_time)
            return await self.wait()

        self.calls.append(datetime.now())



async def create_description_of_article(article, rate_limiter=None):
    """
    Calls LLM to create description section, chapter or an article
    """
    # Ждем разрешения от RateLimiter

    prompt = """Представь, что ты юрист, который должен объяснить 18-летнему клиенту суть статьи из кодекса законов. 
Твоя задача - изложить основные положения статьи простым и понятным языком, избегая сложной юридической терминологии. 
Сфокусируйся на ключевых моментах и практических последствиях применения этой статьи, приведи примеры из реальной жизни, если это уместно. 
Постарайся уместить свое объяснение в 5-7 предложений, чтобы молодой человек мог легко понять и запомнить главную информацию.
<article>
{ARTICLE}
</article>
""".format(ARTICLE=article)
    
    description = await send_message_to_gemini_async(prompt, rate_limiter=rate_limiter)
    return description


async def create_short_description_of_article(article, rate_limiter=None):
    """
    Calls LLM to create short description section, chapter or an article
    """

    prompt = """Твоя задача - изложить основные положения статьи простым и понятным языком, избегая сложной юридической терминологии. 
Перечисли списком штрафы за какие типы нарушений обсуждаются в статье, просто перечисли сами нарушения, без детализации.
Постарайся уместить свое объяснение в несколько предложений. Самую важную и общую информацию приведи в начале.
<article>
{ARTICLE}
</article>
""".format(ARTICLE=article)
    
    description = await send_message_to_gemini_async(prompt, rate_limiter=rate_limiter)
    return description


async def create_description_of_chapter(chapter_title, articles, rate_limiter=None):
    """
    Calls LLM to create description chapter, chapter or an article
    """
    # Ждем разрешения от RateLimiter
    articles_json_str = json.dumps(articles, ensure_ascii=False, indent=2)

    prompt = """Ты професиональный юрист который простыми словами объясняет суть главы из КОАП РФ. 
Твое объяснение главы должно быть полным и упоминать все статьи находящиеся в ней.
Я дам тебе наименование главы и список статьей с их кратким описанием.
Твоя задача - изложить основные положения главы КОАП простым и понятным языком, избегая сложной юридической терминологии. 
Сфокусируйся на ключевых моментах и практических последствиях применения этой статьи.
<articles>
{chapter_title}
{ARTICLES}
</articles>
""".format(ARTICLES=articles_json_str, chapter_title=chapter_title)
    
    description = await send_message_to_gemini_async(prompt, rate_limiter=rate_limiter)
    return description


async def process_and_save_article_descriptions(coap_json, base_path, rate_limiter):
    tasks = []
    for section in coap_json.keys():
        section_path = os.path.join(base_path, section)
        for chapter in coap_json[section]:
            chapter_path = os.path.join(section_path, chapter)
            for article, article_text in coap_json[section][chapter].items():
                article_path = os.path.join(chapter_path, article)

                # create description.txt of articles
                # article_description_path = os.path.join(article_path, 'description.txt')
                # if os.path.exists(article_description_path): continue
                # task = asyncio.create_task(
                #     create_and_write_article_description(article_text, article_description_path, rate_limiter))
                # tasks.append(task)
                
                # create short_description.txt of articles
                short_article_description_path = os.path.join(article_path, 'short_description.txt')
                # if os.path.exists(short_article_description_path): continue
                task = asyncio.create_task(
                    create_and_write_short_article_description(article_text, short_article_description_path, rate_limiter))
                tasks.append(task)

    await asyncio.gather(*tasks)


async def process_and_save_chapter_descriptions(nested_json, base_path, rate_limiter, rewrite=False):
    """
    создаем description.txt для глав
    """

    tasks = []
    for section_title in nested_json['childs']:
        for chapter_title in nested_json['childs'][section_title]['childs']:
            chapter_description_path = os.path.join(base_path, section_title, chapter_title, 'description.txt')

            chapter = nested_json['childs'][section_title]['childs'][chapter_title]
            articles = {}
            # собрать все статьи из главы для суммаризации главы
            for article in chapter['childs'].keys():
                if len(chapter['childs'].keys()) > 15: # если больше 15 статей то используем короткие описания
                    articles[article] = chapter['childs'][article]['short_description']
                else:
                    articles[article] = chapter['childs'][article]['description']

            # if not rewrite:
            #     if os.path.exists(chapter_description_path): continue
            task = asyncio.create_task(
                create_and_write_chapter_description(articles, chapter_description_path, rate_limiter))
            tasks.append(task)

    await asyncio.gather(*tasks)


async def create_and_write_chapter_description(articles, chapter_description_path, rate_limiter):
    description = await create_description_of_chapter(chapter_description_path, articles, rate_limiter)
    # if description is not None:
    await save_description_to_file(description['text_response'], chapter_description_path)
    print('Saved description to:', chapter_description_path)


async def create_and_write_article_description(article_text, description_path, rate_limiter):
    description = await create_description_of_article(article_text, rate_limiter)
    # if description is not None:
    await save_description_to_file(description['text_response'], description_path)
    print('Saved description to:', description_path)


async def create_and_write_short_article_description(article_text, description_path, rate_limiter):
    description = await create_short_description_of_article(article_text, rate_limiter)
    # if description is not None:
    await save_description_to_file(description['text_response'], description_path)
    print('Saved short description to:', description_path)



async def main():
    base_path = 'coap_map'
    
    file_path = 'COAP.txt'
    with open(file_path, 'r') as file:
        coap_txt = file.read()
    coap_json = create_nested_json(coap_txt)
    create_folder_structure(base_path, coap_json)

    # rate_limiter = RateLimiter(5, 6)  # Лимит 5 запросов в 6 секунд (лимит 60 запросов в минуту)
    rate_limiter = RateLimiter(9, 10)  # Лимит 9 запросов в 10 секунд (лимит 60 запросов в минуту)

    # STEP ARTICLE descriptions
    await process_and_save_article_descriptions(coap_json, base_path, rate_limiter)

    # STEP CHAPTER descriptions
    # created chapter descriptions from article descriptions
    # nested_json = dir_to_json_with_txt_content(base_path)
    # await process_and_save_chapter_descriptions(nested_json, base_path, rate_limiter, rewrite=True)


if __name__ == "__main__":
    asyncio.run(main())

