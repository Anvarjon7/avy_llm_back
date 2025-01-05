from flask import Flask, request, jsonify
from services import mq_listener, file_processor, chunk_manager, llm_api, mq_producer
from database.mongo_handler import MongoHandler
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
        elif any(file_path.lower().endswith(ext) for ext in video_extensions):
            text = file_processor.process_video(file_path)   
        else:
            print("Unsupported file type")    
            return
    
        if not text:
            print("File processing failed")
        summary = llm_api.get_summary_from_llm(text)
        mq_producer.send_to_the_queue(summary,lesson_id)
        chunks = chunk_manager.split_text_into_chunks(text)
        db_handler.insert_lesson_chunks(lesson_id, chunks)
        print(f"Chunks stored for lesson {lesson_id}")
    except Exception as e:
        print(f"Error processing incoming message: {e}")


mq_conn = mq_listener.start_listener(
    ACTIVE_MQ_URL=os.getenv("ACTIVE_MQ_URL"), 
    queue=os.getenv("LESSON_QUEUE"),
    process_callback=process_incoming_message
    )

# Receives a question from the user, retrieves the corresponding context from the database, 
# queries the LLM for an answer, and returns the response.
@app.route("/ask-question", methods=['POST'])
def ask_question():
    data = request.get_json()
    lesson_id = data.get("lesson_id")
    question = data.get("question")

    if not lesson_id or not question:
        return jsonify({"error": "lesson_id and question are required"}), 400
    
    chunks = db_handler.get_lesson_chunks(lesson_id)
    if not chunks:
        return jsonify({"error": "Lesson not found"}), 404
    
    context = " ".join(chunks)
    if len(context.split()) > 2000: #Limit context to approx. 2000 tokens
        context = " ".join(context.split()[:2000])

    try:
        answer = llm_api.get_response_from_llm(context,question)
        return jsonify({"answer":answer})
    except Exception as e:
        print(f"Error generating LLM response: {e}")
        return jsonify({"error": "Failed to generate answer"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
