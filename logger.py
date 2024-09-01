# logger.py

import os
import datetime
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

class Logger:
    def __init__(self,credentials_path, log_file_name='bot_logs.txt', max_logs=25920):
        self.credentials_path = credentials_path
        self.log_file_name = log_file_name
        self.max_logs = max_logs
        self.ensure_file_exists()
        
        with open(self.credentials_path, 'r') as file:
            self.credentials = json.load(file)
        
    def ensure_file_exists(self):
        if not os.path.exists(self.log_file_name):
            with open(self.log_file_name, 'w',encoding='utf-8') as f:
                f.write("")

    def log(self, message,botUser):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message} {botUser}\n"
        
        # Add the log to the end of the file
        with open(self.log_file_name, 'a',encoding='utf-8') as f:
            f.write(log_message)
        
        # Check if the log lines exceed max_logs and truncate if necessary
        self.truncate_logs()

    def truncate_logs(self):
        with open(self.log_file_name, 'r') as f:
            lines = f.readlines()

        if len(lines) > self.max_logs:
            with open(self.log_file_name, 'w') as f:
                f.writelines(lines[-self.max_logs:])

    def display(self, message,botUser):
        # Print to console
        print(message, botUser)
        # Also log the message
        self.log(message,botUser)

    def send_exception_mail(self,exception):

            mailAddress = self.credentials['mailInfo']['mailAddress']
            password = self.credentials['mailInfo']['password']
            sendTo = self.credentials['mailInfo']['sendToException']

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Binance Trading Bot: {exception}"
            msg["From"] = mailAddress
            msg["To"] = sendTo
            msg.attach(MIMEText(f"An exception occurred: {exception}", "plain"))

            mail = smtplib.SMTP("smtp-mail.outlook.com", port=587)
            mail.set_debuglevel(1)
            mail.ehlo()
            mail.starttls()
            mail.login(mailAddress, password)
            mail.sendmail(mailAddress, sendTo, msg.as_string())
                
