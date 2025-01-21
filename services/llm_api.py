import openai

from config import Config
import os
from database.mongo_handler import MongoHandler
from dotenv import load_dotenv


load_dotenv()

openai.api_key = Config.OPENAI_API_KEY
openai.api_key = os.getenv("OPENAI_API_KEY")
db_handler = MongoHandler(uri=os.getenv("MONGO_URI"), db_name=os.getenv("DB_NAME"))

def get_summary_from_llm(context):
    messages = [
        {"role": "system","content":
            "You are a helpful assistant and must provide a brief but informative summary of the context(your answer must be strictly up to 500 characters!)"},
        {"role": "user", "content": f"Context: {context}"}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150
    )
    print("result: " + response.choices[0].message["content"].strip())
    return response.choices[0].message["content"].strip()

def get_response_from_llm(user,user_input):
 try:
    user_id = user.get("user_id")
    lesson_id = user.get("lesson_id")
    conversation_tracker = user.get("conversation_history")
    conversation_tracker.append(
        {
            "role": "user",
            "content": f"User input:{user_input}"
        }
    )
    print("course tracker appended")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation_tracker,
        max_tokens=150
    ).choices[0].message["content"].strip()
    print(response)
    conversation_tracker.append(
        {
            "role": "assistant",
            "content": response
        }
    )
    print(conversation_tracker)
    db_handler.insert_user_data(user_id,lesson_id,conversation_tracker)
    return response
 except Exception as e:
      print(f"Error querying LLM: {e}")
