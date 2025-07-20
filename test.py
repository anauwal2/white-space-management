import smtplib
from email.mime.text import MIMEText

sender = "admin@orbiberjangka.com"
receiver = "oyamasenshio@gmail.com"
password = "urxi zncs clcv qozf"  # NOT your Gmail password

msg = MIMEText("This is the email body.")
msg["Subject"] = "Test Email"
msg["From"] = sender
msg["To"] = receiver

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(sender, password)
    server.send_message(msg)

print("Email sent successfully!")
