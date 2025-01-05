import json
import os
import stomp
queue=os.getenv("LESSON_SUMMARY_QUEUE")
broker_host=os.getenv("ACTIVE_MQ_URL")
def send_to_the_queue(summary,lesson_id):
    print(f"Sending summary: {summary}")
    data = {"summary": summary, "lessonId": lesson_id}
    conn = stomp.Connection([(broker_host,61613)])
    conn.connect()
    conn.send(queue,json.dumps(data))
    print("message sent")
    conn.disconnect()