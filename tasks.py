import time
from celery_app import celery_app

@celery_app.task(name="tasks.send_mock_email")
def send_mock_email(email:str):
    time.sleep(10)
    print(f"Email sent to {email}")