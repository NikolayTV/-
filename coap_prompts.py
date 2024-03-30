from parallel_descriptions import send_message_to_gemini_async



async def get_perefrased_query(USER_QUERY, ):

    prompt = """Перефразируй вопрос сделав его более понятным. Расширь вопрос 3 уточнениями чтобы лучше раскрывать тему с разных сторон. Выведи только вопросы в списке без комментариев.
Формат вывода: ["перефразированный вопрос", "уточняющий вопрос 1", "уточняющий вопрос 2"]
Вот попрос:
<query>{USER_QUERY}</query>
""".format(USER_QUERY=USER_QUERY)
    description = await send_message_to_gemini_async(prompt, attempt=1, max_attempts=10)
    return description
