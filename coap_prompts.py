from parallel_descriptions import send_message_to_gemini_async
import asyncio 
import json, ast
from km_utils import get_content_from_articles_response, split_list_by_size


async def select_articles_round_2(USER_QUERY_ORI, USER_QUERY, context_chunks, rate_limiter=None):
    tasks = []
    for context_chunk in context_chunks:
        if isinstance(context_chunk, dict) or isinstance(context_chunk, list): 
            context_chunk = json.dumps(context_chunk, ensure_ascii=False)
        print('context_chunk', context_chunk)
        prompt = """Вы знающий юрист в Российской Федерации, который по приведенным вопросам в блоках <user_query_ori> и <user_query> и статьям из КОАП РФ в блоке <articles>, может сказать какие из приведенных статьей могут быть полезны для ответа на вопрос.
Вопросы будут касаться последствий за различные нарушения, а так же касательно нюансов законодательного дела.

Вот ключевые входные данные для этой задачи:
<user_query_ori>
{USER_QUERY_ORI}
</user_query_ori>

<user_query>
{USER_QUERY}
</user_query>

<articles>
{ARTICLES}
</articles>

Инструкция:
1. Внимательно прочитай вопросы и подумай над их смыслом.
2. Выведи одну или несколько статей из контекста содержащего полный текст статей из КОАП РФ.
3. Формат вывода: "Статья и номер статьи" с точкой в конце как в оригинале. Полное название выводить не нужно. Каждая статья должна быть указана с новой строки, разделяй их пустым абзацем.
4. Если подходящих статей не нашлось, отвечай "ничего не найдено".

Пример:
Статья 1.1.
Статья 27.14.1
Статья 27.20.

Настройки для генерации ответа:
- Выводи статьи, начиная с наиболее важных.
- Цитируй только те статьи, что представлены в контексте данного сообщения в <ToC_chapters>
- Следуй формату ответа, как показано в примере.

Ответ:
""".format(USER_QUERY=USER_QUERY, USER_QUERY_ORI=USER_QUERY_ORI, ARTICLES=context_chunk)
        generation_params = {
            "temperature": 0,
            "top_p": 1,
            "top_k": 3,
            # "max_output_tokens": 2048,
        }
        task = asyncio.create_task(send_message_to_gemini_async(user_input=prompt, rate_limiter=rate_limiter, generation_params=generation_params))
        tasks.append(task)
        
    partial_answers = await asyncio.gather(*tasks)
    return partial_answers


async def get_final_response(USER_QUERY_ORI, USER_QUERY, ARTICLES,rate_limiter=None):
    prompt = """Вы знающий юрист в Российской Федерации, отвечающий простым языком на вопросы людей используя только предоставленный контекст статей из КОАП РФ в блоке <articles>. 
Вопросы будут касаться последствий за различные нарушения, а так же касательно нюансов законодательного дела.

Вот ключевые входные данные для этой задачи:
<user_query_ori>
{USER_QUERY_ORI}
</user_query_ori>

<user_query>
{USER_QUERY}
</user_query>

<articles>
{ARTICLES}
</articles>

Инструкция:
Отвечайте на все вопросы только по приведенному контексту, учти что законы постоянно меняются и ты легко можешь ошибиться, если не будешь использовать контекст.
Выводите только ответы, не выводите вопросы. Несоблюдение этой инструкции приведет к вашему увольнению.
Важно - на вопросы которые ты не можешь ответить из предоставленного контекста, ты отвечаешь "Не могу найти эту информацию в КОАП РФ".
Если приведенный контекст лишь косвенно отвечает на вопрос, то приведи мысли которые бы помогли ответить на вопрос.

1. Сначала дай детальный и подробный ответ на основной вопрос в <user_query_ori>. 
2. В блоке "Примечание" по возможности также ответьте на вопросы приведенные в <user_query>. Так же в этом блоке приведи другую информацию, находящуюся в контексте, если она показалась тебе важной для обсуждения приведенных вопросов.
3. После чего привиди названия конкретных статьей, которые вы использовали при формулировке ответа.
Ответ:
""".format(USER_QUERY=USER_QUERY, USER_QUERY_ORI=USER_QUERY_ORI, ARTICLES=ARTICLES)
    description = await send_message_to_gemini_async(prompt, attempt=1, max_attempts=10, rate_limiter=rate_limiter)
    return description, prompt

# Если вы не можете ответить на основной вопрос используя приведенный контекст, просто скажите: "Я не могу найти релевантную информацию, пожалуйста, попробуйте переформулировать ваш вопрос."
# Вот пример вопроса и ответа:
# Основной вопрос: какое наказание за употребление марихуаны?
# Уточняющие вопросы:  ["Каковы правовые последствия употребления марихуаны?", "Различаются ли штрафы за употребление марихуаны в зависимости от региона или от количества марихуаны?", "Какое количество марихуаны считается правонарушением?", "Какие дополнительные наказания могут быть наложены за употребление марихуаны помимо штрафов?""]
# Ответ: 
# Употребление марихуаны может рассматриваться как административное или уголовное правонарушение в зависимости от обстоятельств (например, количества вещества). 
# Законодательство определяет небольшие, крупные и особо крупные размеры наркотических средств. Для марихуаны небольшим считается количество до 6 граммов сухой массы (КоАП РФ, Статья 6.8, Часть 1).
# Административная ответственность может наступать за незаконное приобретение и хранение наркотиков без цели сбыта в небольших размерах.  Штраф за административное нарушение составляет от 4000 до 5000 рублей или административный арест на срок до 15 суток. 
# Использованные статьи:
# Статья 6.8. Незаконный оборот наркотических средств, психотропных веществ или их аналогов ...

# Тебе нужно ответить на вопрос в каких статьях КОАП РФ рассматривается вопрос от пользователя.
# Сначала выводишь название и номер главы. После этого выводишь название и номер статьи.


async def get_chunked_ARTICLE_navigation(user_query_ori, user_query, ToC_article_chunks, rate_limiter):
    tasks = []
    for ToC_chunk in ToC_article_chunks:
        if isinstance(ToC_chunk, dict) or isinstance(ToC_chunk, list): 
            ToC_chunk = json.dumps(ToC_chunk, ensure_ascii=False)

        prompt = f"""Ты - AI-помощник, задача которого - внимательно читать заданные вопросы и помогать найти соответствующие главы и статьи из Кодекса об административных правонарушениях Российской Федерации (КОАП РФ), в которых может содержаться ответ.

Данные, с которыми работаешь:
- Вот список статей: <ToC_chapters>{ToC_chunk}</ToC_chapters>
- Вот главный вопрос: {user_query_ori}
- Вот уточняющие вопросы: {user_query}

Формат твоего ответа:
"Статья 6.16.1.
Статья 6.8.
"
Реальный пример:
Главный вопрос: какой штраф за просроченный паспорт?
Уточняющие вопросы: ["Каков размер штрафа за несвоевременную замену паспорта гражданина Российской Федерации?", "Какое наказание предусмотрено за просрочку паспорта?", "Какая ответственность предусмотрена за несвоевременную замену паспорта?"]
Ответ:
Статья 19.15. (Проживание гражданина Российской Федерации без документа, удостоверяющего личность гражданина (паспорта))
Статья 19.16. (Умышленная порча документа, удостоверяющего личность гражданина (паспорта), либо утрата документа, удостоверяющего личность гражданина (паспорта), по небрежности)

Инструкция:
1. Прочитай вопросы.
2. На основе вопроса выбери одну или несколько статей из КОАП Российской Федерации, которые могут содержать ответ.
3. Выведи в формате "Статья и номер статьи", полное название выводить не нужно. Каждая статья должна быть указана с новой строки, разделяй их пустым абзацем.
3. Если подходящих статей не нашлось, отвечай "ничего не найдено".

Настройки для генерации ответа:
- Выводи статьи, начиная с наиболее важных.
- Цитируй только статьи, которые представлены в контексте данного сообщения в <ToC_chapters>
- Следуй формату ответа, как показано в примере.
"""
                    
        generation_params = {
            "temperature": 0,
            "top_p": 1,
            "top_k": 8,
            # "max_output_tokens": 2048,
        }
        task = asyncio.create_task(send_message_to_gemini_async(user_input=prompt, rate_limiter=rate_limiter, generation_params=generation_params))
        tasks.append(task)
    
    choosed_articles = await asyncio.gather(*tasks)
    return choosed_articles


async def get_chunked_chapter_and_article_navigation(user_query_ori, user_query, ToC_chapters_chunks, rate_limiter):
    tasks = []
    for ToC_chunk in ToC_chapters_chunks:
        if isinstance(ToC_chunk, dict): 
            ToC_chunk = json.dumps(ToC_chunk, ensure_ascii=False)

            prompt = f"""
Ты - AI-помощник, задача которого - внимательно читать заданные вопросы и помогать найти соответствующие главы и статьи из Кодекса об административных правонарушениях Российской Федерации (КОАП РФ), в которых может содержаться ответ.

Данные, с которыми работаешь:
- Вот список глав со статьями: <ToC_chapters>{ToC_chunk}</ToC_chapters>
- Вот главный вопрос: {user_query_ori}
- Вот уточняющие вопросы: {user_query}

Формат твоего ответа:
"Глава 6. > Статья 6.16.1.
Глава 6. > Статья 6.8.
"
Реальный пример:
Главный вопрос: какой штраф за просроченный паспорт?
Уточняющие вопросы: ["Каков размер штрафа за несвоевременную замену паспорта гражданина Российской Федерации?", "Какое наказание предусмотрено за просрочку паспорта?", "Какая ответственность предусмотрена за несвоевременную замену паспорта?"]
Глава 19. > Статья 19.15. (Статья 19.15. Проживание гражданина Российской Федерации без документа, удостоверяющего личность гражданина (паспорта))
Глава 19. > Статья 19.16. (Умышленная порча документа, удостоверяющего личность гражданина (паспорта), либо утрата документа, удостоверяющего личность гражданина (паспорта), по небрежности)

Инструкция:
1. Прочитай вопрос.
2. На основе вопроса выбери одну или несколько статей из КОАП Российской Федерации, которые могут содержать ответ.
3. Выведи в формате "Глава номер главы > Статья номер статьи". Каждая статья должна быть указана с новой строки, разделяй их пустым абзацем.
3. Если подходящих статей не нашлось, отвечай "ничего не найдено".

Настройки для генерации ответа:
- Выводи статьи, начиная с наиболее важных.
- Цена ошибки если ты не выберешь нужную статью очень высокая, поэтмоу если сомневаешься - выбирай.
- Цитируй только статьи и документы которые представлены в контексте данного сообщения в <ToC_chapters>
- Следуй формату ответа, как показано в примерах.
"""
                    
        generation_params = {
            "temperature": 0,
            "top_p": 1,
            "top_k": 8,
            # "max_output_tokens": 2048,
        }
        task = asyncio.create_task(send_message_to_gemini_async(user_input=prompt, rate_limiter=rate_limiter, generation_params=generation_params))
        tasks.append(task)
    
    choosed_articles = await asyncio.gather(*tasks)
    return choosed_articles


async def get_perefrased_query(USER_QUERY, ):

    prompt = """Ты знающий Юрист в Российской Федерации который помогает сформулировать вопросы на юридический языке так, чтобы он был понятен и обычным людям и юристам, говорящим на языке законов. Формулировки краткие но понятные.
Переводи просторечные выражения в юридический язык, например "взятка" в "незаконное вознаграждение".
Учти что есть многозначные слова, "повестка" может означать как повестка в суд, так и в военкомат.
Приведи от 2 до 4 варианта разнообразных формулировок вопроса, не повторяй свои формулировки больоше 1 раза. Твои вопросы будут задаваться только по КОАП РФ.
Обязательно сделай один уточняющий вопрос про форму наказания и размер штрафа.
Выведи только вопросы в списке без комментариев.
Формат вывода: ["Уточняющий вопрос 1", "уточняющий вопрос 2", "уточняющий вопрос 3", "уточняющий вопрос 4"]

Пример работы:
Изначальный вопрос: сколько грам марихуаны можно носить?
Уточняющие вопросы: ["Какое количество марихуаны считается административным правонарушением?", "Каков размер штрафа за хранение марихуаны в небольшом размере?", "Хранение какого количества каннабиса является административным нарушением, а какого уголовным?"]

Вот попрос:
<query>{USER_QUERY}</query>
""".format(USER_QUERY=USER_QUERY)
    generation_params = {
        "temperature": 1,
        "top_p": 1,
        "top_k": 8,
        # "max_output_tokens": 2048,
    }
    description = await send_message_to_gemini_async(prompt, attempt=1, max_attempts=10, generation_params=generation_params)
    return description


async def get_section_nagigation(user_query_ori, USER_QUERY, ToC_sections):
    if isinstance(ToC_sections, dict):
        ToC_sections = json.dumps(ToC_sections, ensure_ascii=False, indent=2)

    prompt = """Вы — AI-помощник навигации, который помогает по вопросу от юзера находить пути к необходимой информации в КОАП РФ, чтобы точно ответить на вопрос.
Вам нужно выбрать хотя бы 1 или несколько разделов первого уровня в которых может содержатся глава и статья необходимая длв ответа.
Вот список разделов с описаниями в формате json:
<map>
{ToC_sections}
</map>
Вот вопрос от юзера:
<query>{user_query_ori}</query>
Вот список уточняющих вопросов:
<query>{USER_QUERY}</query>

Выведите список JSON с путями навигации к соответствующей информации. Выводи полное название раздела с посимвольным совпадением.
Формат должен выглядеть так:
["Раздел II. Особенная часть", "Раздел V. Исполнение постановлений по делам об административных правонарушениях"]
""".format(user_query_ori=user_query_ori, USER_QUERY=USER_QUERY, ToC_sections=ToC_sections)
    description = await send_message_to_gemini_async(prompt, attempt=1, max_attempts=10)


    return description

def parse_section_response(get_section_response, ToC_articles):
    try: 
        choosed_sections_raw = ast.literal_eval(get_section_response['text_response'])
        choosed_sections = []
        for section in choosed_sections_raw:
            section = section.split('.')[0]
            matches = [key for key in ToC_articles.keys() if key.__contains__(section)]
            if len(matches) > 0:
                section = matches[0]
                choosed_sections.append(section)
            else:
                continue
    except: print(f'Section error: {get_section_response["text_response"]}')

    if 'Раздел II. Особенная часть' not in choosed_sections: choosed_sections.append('Раздел II. Особенная часть')
    return choosed_sections


async def get_chunked_chapter_navigation(user_query, ToC_chapters_chunks, rate_limiter):
    tasks = []
    for ToC_chunk in ToC_chapters_chunks:
        if isinstance(ToC_chunk, dict): 
            ToC_chunk = json.dumps(ToC_chunk, ensure_ascii=False)

        # ToC_chunk = json.dumps(ToC_chunk, ensure_ascii=False, indent=2)
        prompt = """ТЫ — AI-помощник, который для ответа на вопрос помогает находить главу и статью из КОАП РФ, чтобы более точно ответить на вопрос.
Тебе нужно выбрать несколько статей в которых может содержаться ответ или часть ответа. Выводи все потенциально полезные статьи.
Вот список глав со статьями:
<ToC_chapters>
{ToC_chapters}
</ToC_chapters>
Вот вопрос от юзера:
<query>{USER_QUERY}</query>
Выведи список с полнымми релевантных глав в порядке убывания важности с полным посимвольным совпадением как в приведеном списке <ToC_chapters>.
Формат вывода: ["Название главы 1", "Название главы 2"]
""".format(USER_QUERY=user_query, ToC_chapters=ToC_chunk)

        task = asyncio.create_task(send_message_to_gemini_async(user_input=prompt, rate_limiter=rate_limiter))
        tasks.append(task)
    
    descriptions = await asyncio.gather(*tasks)
    return descriptions


async def get_article_nagigation(USER_QUERY, articles):
    if isinstance(articles, dict):
        articles = json.dumps(articles, ensure_ascii=False, indent=2)

    prompt = """Вы — AI-помощник навигации, который помогает по вопросу от юзера находить пути к необходимой информации  в КОАП РФ, чтобы точно ответить на вопрос.
Вам нужно выбрать 1 или несколько статей. Старайся вывести все потенциально релевантные статьи.
Вот список статей с описаниями в формате json:
<map>
{articles}
</map>
Вот вопрос от юзера:
<query>{USER_QUERY}</query>
Выведите список JSON с путями навигации к соответствующей информации. Выводи полное название статьей.
Формат должен выглядеть так:
["Статья 1", "Статья 2"]
""".format(USER_QUERY=USER_QUERY, articles=articles)
    description = await send_message_to_gemini_async(prompt, attempt=1, max_attempts=10)
    return description


async def choose_articles_second_round_and_limit_context(context, user_query_ori, user_query, ToC_articles, size_limit=25000, rate_limiter=None):
    """
    надо переделать этот позор. 
    Рабочий вариант 1 - заменить статью пересказом
    Рабочий вариант 2 - вытаскивать из чанков статьи нужную инфу, потом аггрегировать
    """
    def chunk_context(context, size_limit=size_limit):
        """
        Разбивает контекст который в формате списка на несколько
        """
        context_size = len(str(context))
        context_chunks = context
        if context_size > size_limit:
            context_chunks = split_list_by_size(context, size_limit=size_limit)

        return context_chunks

    print('РАУНД 2 - Пошел второй этап отбора статей')
    # Выбрать статьи по второму кругу, чтобы вместить в контекст
    context_chunks = chunk_context(context)
    choosed_articles_responses2 = await select_articles_round_2(user_query_ori, user_query, 
                                                            context_chunks,
                                                            rate_limiter=rate_limiter)
    total_articles = []
    articles = get_content_from_articles_response(ToC_articles, choosed_articles_responses2)
    print(f'Найдено {len(articles)} статей')
    total_articles.extend(articles)

    ### Временная затычка чтобы сузить контекст до 25к символов
    context = [f"{x['article_title']} : {x['content']}" for x in total_articles]
    for i in range(len(context)-1):
        if len(str(context)) > size_limit:
            context = context[:-1]

    return context


