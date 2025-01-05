import openai
from config import Config
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = Config.OPENAI_API_KEY

# Sends the context (combined chunks) and the user's question to OpenAI GPT-3.5-turbo and retrieves the response.
def get_response_from_llm(context, question):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    messages = [
        {"role": "system",
         "content": "You are a helpful assistant and must answer only to questions related to the context. If question is irrelevant just you must tell the user: I cannot answer, questions asked should be relevant to your lesson"},
        {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
    ]

    try:
        response = openai.ChatCompletion.create(
            model ="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print(f"Error querying LLM: {e}")
        return None