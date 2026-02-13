"""
Legacy Email Handler - Old SMTP implementation
This file contains hardcoded SMTP password and email addresses - should be BLOCKED
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailHandler:
    def __init__(self):
        # Hardcoded SMTP credentials - SECURITY VIOLATION
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.smtp_username = "legacy-app@company.com"
        self.smtp_password = "emailpass456"  # Hardcoded password!

        # Hardcoded recipient emails - SECURITY VIOLATION
        self.admin_email = "admin@company.com"
        self.support_email = "support@company.com"

    def connect_to_smtp(self):
        """Establish SMTP connection with hardcoded credentials"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            return server
        except Exception as e:
            print(f"Failed to connect to SMTP: {e}")
            return None

    def send_welcome_email(self, user_email, username):
        """Send welcome email to new user"""
        server = self.connect_to_smtp()
        if not server:
            return False

        msg = MIMEMultipart()
        msg['From'] = self.smtp_username
        msg['To'] = user_email
        msg['Subject'] = "Welcome to Our Service!"

        body = f"""
        Hello {username},

        Welcome to our service! We're glad to have you.

        If you need help, contact us at {self.support_email}

        Best regards,
        The Team
        """

        msg.attach(MIMEText(body, 'plain'))

        try:
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def send_admin_notification(self, subject, message):
        """Send notification to admin"""
        server = self.connect_to_smtp()
        if not server:
            return False

        msg = MIMEMultipart()
        msg['From'] = self.smtp_username
        msg['To'] = self.admin_email  # Hardcoded admin email
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'plain'))

        try:
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False

    def send_password_reset(self, user_email, reset_token):
        """Send password reset email"""
        server = self.connect_to_smtp()
        if not server:
            return False

        reset_link = f"https://app.company.com/reset?token={reset_token}"

        msg = MIMEMultipart()
        msg['From'] = self.smtp_username
        msg['To'] = user_email
        msg['Subject'] = "Password Reset Request"

        body = f"""
        You requested a password reset.

        Click here to reset your password: {reset_link}

        If you didn't request this, please contact {self.support_email}
        """

        msg.attach(MIMEText(body, 'plain'))

        try:
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Failed to send reset email: {e}")
            return False


# Example usage
if __name__ == "__main__":
    handler = EmailHandler()
    handler.send_welcome_email("newuser@example.com", "John")
