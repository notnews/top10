#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from configparser import ConfigParser


class Notification():
    def __init__(self, cfgfile="email.cfg"):
        config = ConfigParser()
        config.read(cfgfile)
        self.smtp_server = config.get('notification', 'smtp_server')
        self.smtp_port = config.get('notification', 'smtp_port')
        self.smtp_user = config.get('notification', 'smtp_user')
        self.smtp_pass = config.get('notification', 'smtp_pass')
        self.smtp_ssl = config.getboolean('notification', 'smtp_ssl')
        self.email_from = config.get('notification', 'email_from')
        self.email_to = config.get('notification', 'email_to').split(',')

    def send_email(self, subject, text, attachment=None):
        logging.info("Sending email: [%s] to %s" % (subject, self.email_to))

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = self.email_from
        msg['To'] = ', '.join(self.email_to)

        msg.attach(MIMEText(text))

        if attachment:
            with open(attachment, 'rb') as f:
                part = MIMEBase('text', "plain")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="{0:s}"'.format(attachment))
                msg.attach(part)

        try:
            if self.smtp_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)                
            server.set_debuglevel(1)
            server.ehlo()
            if self.smtp_user != '':
                server.login(self.smtp_user, self.smtp_pass)
            server.sendmail(self.email_from, self.email_to, msg.as_string())

            server.quit()
        except Exception as e:
            logging.error("Cannot send email: %r" % e)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        notification = Notification(sys.argv[1])
    else:
        notification = Notification()

    notification.send_email('Test Email', 'This is test e-mail.')
