import smtplib
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler
import os
import datetime

# Initialize the scheduler
scheduler = BackgroundScheduler()

def send_email_reminder(email: str, task_desc: str):
    """
    Sends an email reminder for a specific task.
    """
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"Mock Email sent to {email}: Reminder for task '{task_desc}'")
        return

    msg = MIMEText(f"Hello, this is a reminder to work on your task: {task_desc}")
    msg['Subject'] = 'AI Mentor Task Reminder'
    msg['From'] = SMTP_USER
    msg['To'] = email

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {email} for task '{task_desc}'")
    except Exception as e:
        print(f"Failed to send email: {e}")

def schedule_reminders_for_user(email: str, tasks: list, start_date: datetime.date):
    """
    Schedules reminders based on the week-by-week roadmap.
    """
    for task in tasks:
        # For prototype: assume 1 week = 7 days offset
        run_date = start_date + datetime.timedelta(days=task.week * 7)
        scheduler.add_job(
            send_email_reminder, 
            'date', 
            run_date=run_date, 
            args=[email, task.task]
        )

def start_scheduler():
    scheduler.start()
