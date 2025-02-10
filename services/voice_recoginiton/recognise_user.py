import os
import numpy as np
from scipy.spatial.distance import cosine
from database.mongo_handler import MongoHandler
from services.voice_recoginiton.extract_embeddings import extract_embedding


# Load stored embeddings
db_handler = MongoHandler(uri=os.getenv("MONGO_URI"), db_name=os.getenv("DB_NAME"))
def recognize_user(new_sample):
    new_embedding = extract_embedding(new_sample)

    best_match = None
    lowest_distance = float("inf")  # Start with a high distance
    for user in db_handler.find_all_voice_embeddings():
        stored_embedding = np.array(user["embedding"]) # Convert back to NumPy
        distance = cosine(new_embedding, stored_embedding)  # Compute similarity
        print(f"User {user['user_id']} - Similarity Score: {1 - distance:.2f}")

        if distance < lowest_distance:
            lowest_distance = distance
            best_match = user["user_id"]

    if lowest_distance < 0.6:  # Threshold for recognition
        print(f"✅ User recognized as: {best_match}")
        return best_match
    else:
        print("❌ User not recognized!")
        return None

def recognise_concrete_user(new_sample,user_id):
    new_embedding = extract_embedding(new_sample)
    existing_embedding = db_handler.get_embedding_by_user_id(user_id)
    distance = cosine(new_embedding, np.array(existing_embedding))
    print("distance:")
    print(distance)
    if distance < 0.6:
        return True
    else:
        return False