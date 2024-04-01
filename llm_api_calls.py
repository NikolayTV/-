import os
import google.generativeai as genai
import asyncio
from private import GEMINI_API_KEY

def send_message_to_gemini(user_input):
    genai.configure(api_key=GEMINI_API_KEY)
    # genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    generation_config = {
        "temperature": 0.9,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "block_none"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "block_none"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "block_none"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "block_none"},
    ]

    gemini = genai.GenerativeModel(
        model_name="gemini-1.0-pro",  # Или другую модель, например, "models/gemini-1.5-pro"
        generation_config=generation_config,
        safety_settings=safety_settings)

    convo = gemini.start_chat(history=[])
    convo.send_message(user_input)

    gemini_response_text = convo.last.text
    return {"text_response": gemini_response_text, 
            "input_tokens": gemini.count_tokens(user_input), 
            "output_tokens":gemini.count_tokens(gemini_response_text)}
    


async def send_message_to_gemini_async(user_input, rate_limiter=None, attempt=1, max_attempts=10, retry_delay = 1, generation_params={}):
    if rate_limiter is not None: await rate_limiter.wait()

    genai.configure(api_key=GEMINI_API_KEY)
    # genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
    generation_config = {
        "temperature": 0,
        "top_p": 1,
        "top_k": 1,
        # "max_output_tokens": 2048,
    }

    for key, value in generation_params.items():
        generation_config[key] = value

    # BLOCK_ONLY_HIGH block_none
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
    ]

    gemini = genai.GenerativeModel(
        model_name="gemini-1.0-pro",  # Или другую модель, например, "models/gemini-1.5-pro"
        generation_config=generation_config,
        safety_settings=safety_settings)

    try:
        response = await gemini.generate_content_async(
            contents=user_input,
            generation_config=generation_config,
            stream=False,
        )
        if response.candidates[0].finish_reason == 1: # это хороший респонс
            gemini_response_text = response.candidates[0].content.parts[0].text
            return {"text_response": gemini_response_text, 
                    "input_tokens": gemini.count_tokens(user_input), 
                    "output_tokens": gemini.count_tokens(gemini_response_text)}
        else:
            # raise
            print(f'{user_input}, finish resason:', response.candidates[0].finish_reason)
            return {"text_response": f'finish reason: {response.candidates[0].finish_reason}', 
                    "input_tokens": gemini.count_tokens(user_input), 
                    "output_tokens": 0}
        
    except Exception as e:
        if attempt < max_attempts:
            print(f"Error {e}, retrying in {retry_delay} seconds... (Attempt {attempt}/{max_attempts})")
            await asyncio.sleep(retry_delay)
            return await send_message_to_gemini_async(user_input, rate_limiter=rate_limiter,
                attempt=attempt + 1, max_attempts=max_attempts, retry_delay=retry_delay * 2)  # Increase delay for next attempt
        else:
            return {"text_response": " ", 
                    "input_tokens": gemini.count_tokens(user_input), 
                    "output_tokens": 0}


