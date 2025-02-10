import uuid
from crypt import methods

from flask import Flask, request, jsonify
from services import mq_listener, file_processor, chunk_manager, llm_api, mq_producer,live_speech_recogniser
from database.mongo_handler import MongoHandler
from services.llm_api import get_navigation_request
from services.voice_recoginiton.recognise_user import recognize_user, recognise_concrete_user
from services.voice_recoginiton.extract_embeddings import store_embedding
from services.voice_recoginiton.record_voice import record_voice
from utils.validation import validate_message
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
db_handler = MongoHandler(uri=os.getenv("MONGO_URI"), db_name=os.getenv("DB_NAME"))
video_extensions = [".mp4", ".mkv", ".avi", ".mov", ".flv"]

# Handles files (PDF or video), initiates text extraction, and stores chunks in the database.
def process_incoming_message(message):
    try:
        json_message = json.dumps(message)
        data = validate_message(json_message)
        if not data:
            print("Invalid message format")
            return

        file_path = data["filePath"]
        lesson_id = data["lessonId"]

        if file_path.endswith(".pdf"):
            text = file_processor.process_pdf(file_path)
            # print("text: " + text)
        elif any(file_path.lower().endswith(ext) for ext in video_extensions):
            text = file_processor.process_video(file_path)
        else:
            print("Unsupported file type")    
            return
    
        if not text:
            print("File processing failed")
        summary = llm_api.get_summary_from_llm(text)
        print(len(summary))
        mq_producer.send_to_the_queue(summary,lesson_id)
        chunks = chunk_manager.split_text_into_chunks(text)
        db_handler.insert_lesson_chunks(lesson_id, chunks)
        print(f"Chunks stored for lesson {lesson_id}")
    except Exception as e:
        print(f"Error processing incoming message: {e}")

def process_incoming_message_removal(message):
  try:
    json_message = json.dumps(message)
    data = json.loads(json_message)
    if not data:
        print("Invalid message format")
        return
    lesson_id = data["lessonId"]
    db_handler.delete_lesson_chunks(lesson_id)
  except Exception as e:
      print(f"Error processing incoming message: {e}")



mq_conn = mq_listener.start_listener(
    ACTIVE_MQ_URL=os.getenv("ACTIVE_MQ_URL"), 
    queue=os.getenv("LESSON_QUEUE"),
    process_callback=process_incoming_message
    )
mq_conn_2 = mq_listener.start_listener(
    ACTIVE_MQ_URL=os.getenv("ACTIVE_MQ_URL"),
    queue=os.getenv("DELETE_LESSON_CHUNKS_QUEUE"),
    process_callback=process_incoming_message_removal
    )

def get_context(lesson_id):
    chunks = db_handler.get_lesson_chunks(lesson_id)
    if not chunks:
        return jsonify({"error": "Lesson not found"}), 404

    context = " ".join(chunks)
    if len(context.split()) > 2000:  # Limit context to approx. 2000 tokens
        context = " ".join(context.split()[:2000])
    return context
# Receives a question from the user, retrieves the corresponding context from the database, 
# queries the LLM for an answer, and returns the response.
@app.route("/ask-question", methods=['POST'])
def ask_question():
    data = request.get_json()
    lesson_id = data.get("lesson_id")
    question = data.get("question")
    user_id = data.get("user_id")
    print("received question from lms")
    if not lesson_id or not question:
        return jsonify({"error": "lesson_id and question are required"}), 400
    context = get_context(lesson_id)
    try:
        print("about to ask question")
        user = db_handler.get_user_data_for_chatbot(user_id,lesson_id,context)
        answer = llm_api.get_response_from_llm(user,question)
        print("answer: " + answer)
        return jsonify({"answer":answer})
    except Exception as e:
        print(f"Error generating LLM response: {e}")
        return jsonify({"error": "Failed to generate answer"}), 500

@app.route("/ask-verbal-question",methods=['POST'])
def ask_verbal_question():
    data = request.get_json()
    user_id = data.get("user_id")
    print(user_id)
    lesson_id = data.get("lesson_id")
    print("received verbal question from lms")
    audio_file = str(uuid.uuid4()) + ".wav"
    record_voice(audio_file)
    question = live_speech_recogniser.extract_text_from_audio(audio_file)
    if not db_handler.get_user_recognised(user_id,lesson_id):
        result = recognise_concrete_user(audio_file,user_id)
        if not result:
            os.remove(audio_file)
            return jsonify({"answer": "Unfortunately your voice wasn't recognised"})
        else:
            db_handler.insert_user_recognised(user_id,lesson_id,True)
    context = get_context(lesson_id)
    try:
        print("about to ask question")
        user = db_handler.get_user_data_for_chatbot(user_id,lesson_id,context)
        answer = llm_api.get_response_from_llm(user,question)
        print("answer: " + answer)
        os.remove(audio_file)
        return jsonify({"answer":answer})
    except Exception as e:
        print(f"Error generating LLM response: {e}")
        return jsonify({"error": "Failed to generate answer"}), 500

@app.route("/register-voice-pass",methods=['POST'])
def register_voice():
    data = request.get_json()
    user_id = data.get("user_id")
    filename = "user{}.wav".format(user_id)
    record_voice(filename)
    store_embedding(user_id,filename)
    return "created"

@app.route("/voice-pass-login",methods=['POST'])
def recognise_user_by_voice():
   try:
    login_audio_file = str(uuid.uuid4()) + ".wav"
    record_voice(login_audio_file,5)
    result = recognize_user(login_audio_file)
    print(result)
    os.remove(login_audio_file)
    return jsonify({"user_id":result})
   except Exception as e:
       print(f"Error processing voice: {e}")
       return jsonify({"error": e}), 500

@app.route("/request-navigation",methods=['POST'])
def get_voice_input():
    temp_file = str(uuid.uuid4()) + ".wav"
    record_voice(temp_file,5)
    navigation_request = live_speech_recogniser.extract_text_from_audio(temp_file)
    answer = get_navigation_request(navigation_request)
    return jsonify({"answer":answer})



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
    db_handler.default()
