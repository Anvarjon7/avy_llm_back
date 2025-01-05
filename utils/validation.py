import json

# Validates the format and structure of incoming messages from ActiveMQ.
def validate_message(message):
    try:
        print("message : " + message)
        data = json.loads(message)
        if not all(key in data for key in ["filePath", "lessonId"]):
            return None
        return data
    except json.JSONDecodeError:
        return None