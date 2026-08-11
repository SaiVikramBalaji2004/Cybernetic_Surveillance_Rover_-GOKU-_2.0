import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config import EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT, ALERT_SUBJECT, ALERT_BODY

logger = logging.getLogger('GOKU.Email')

class EmailNotifier:
    def __init__(self, sender: str = None, password: str = None, recipient: str = None):
        self.sender = sender or EMAIL_SENDER
        self.password = password or EMAIL_PASSWORD
        self.recipient = recipient or EMAIL_RECIPIENT
        
    def initialize(self) -> bool:
        if not all([self.sender, self.password, self.recipient]):
            logger.warning("Email credentials not configured")
            return False
            
        logger.info("Email notifier initialized")
        return True
    
    def send_alert(self, subject: str = None, body: str = None) -> bool:
        if not all([self.sender, self.password, self.recipient]):
            logger.error("Email not configured")
            return False
            
        subject = subject or ALERT_SUBJECT
        body = body or ALERT_BODY
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = self.recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.sender, self.password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Alert email sent to {self.recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_status(self, status: str) -> bool:
        return self.send_alert(subject="GOKU Status Update", body=status)

email_notifier = EmailNotifier()