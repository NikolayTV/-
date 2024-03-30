import os
import google.generativeai as genai

def send_message_to_gemini(user_input):
    genai.configure(api_key="AIzaSyCEN_JaFKJ9E76p4bSkLz5xJEVdN4eYQLw")
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
    
# send_message_async(
#     content,
#     *,
#     generation_config=None,
#     safety_settings=None,
#     stream=False,
#     **kwargs
# )


# Пример использования функции с пользовательским вводом
send_message_to_gemini("Привет, как дела?")
