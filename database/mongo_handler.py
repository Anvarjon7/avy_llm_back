from pymongo import MongoClient

class MongoHandler:
    def __init__(self, uri, db_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]


    # Saves processed lesson chunks into the MongoDB database.
    def insert_lesson_chunks(self, lesson_id, chunks):
        try:
            collection = self.db["lesson_chunks"]
            document = {"lessonId": lesson_id, "chunks": chunks}
            collection.insert_one(document)
        except Exception as e:
            print(f"Error inserting lesson chunks: {e}")

    # Retrieves saved lesson chunks from the MongoDB database for further use.
    def get_lesson_chunks(self, lesson_id):
        try:
            collection = self.db["lesson_chunks"]
            result = collection.find_one({"lessonId": lesson_id})
            if not result:
                return None
            return result.get("chunks", [])
        except Exception as e:
            print(f"Error retrieving lesson chunks: {e}")
            return None

    def insert_user_data(self,user_id,lesson_id,conversation_data):
        try:
            collection = self.db["user_data"]
            collection.update_one(
                  {"user_id": user_id},
                {"$set": {
                    "lesson_id": lesson_id,
                    "conversation_history": conversation_data}})
        except Exception as e:
          print(f"Error inserting user data: {e}")

    def get_user_data_for_chatbot(self,user_id,lesson_id,context):
        try:
            collection = self.db["user_data"]
            user_document = collection.find_one({"user_id": user_id,"lesson_id":lesson_id})
            if user_document:
                print(user_document.get("user_id"))
                return user_document
            else:
                print("passing the context")
                new_document = {
                    "user_id": user_id,
                    "lesson_id": lesson_id,
                    "conversation_history": [
                        {
                            "role": "system",
                            "content": (
                                "You are a helpful assistant. Your responsibilities are as follows:\n"
                                "1. Answer only questions related to the given text.\n"
                                "2. If the user asks you to ask a question, analyze the text and generate a relevant question.\n"
                                "3. If the user answers your question, compare their answer with the expected answer and provide feedback:\n"
                                "   - If their answer is correct, confirm it.\n"
                                "   - If their answer is incorrect, explain why and provide the correct answer.\n"
                                "4. If the user's question or request is irrelevant to the given text, don't answer and politely inform them that the request is irrelevant.\n"
                                f"Here is the text:{context}."
                            )
                        }
                    ]
                }
                collection.insert_one(new_document)
                user_document = collection.find_one({"user_id": user_id})
                print(user_document.get("conversation_history"))
                return user_document
        except Exception as e:
            print(f"Error retrieving user data: {e}")
            return None