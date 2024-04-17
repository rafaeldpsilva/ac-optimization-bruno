import json
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
import urllib3
from colorama import init, Fore

sys.path.append('.')
init(autoreset=True)


def get_config():
    with open('./config/config.json') as config_file:
        return json.load(config_file)


def update_values_get(process_name, uri):
    response = None
    try:
        request = requests.get(uri)
        data_json = request.text
        response = json.loads(data_json)
    except requests.exceptions.HTTPError:
        print_error("HTTPError in " + process_name)
    except ConnectionRefusedError:
        print_error("ConnectionRefusedError in " + process_name)
    except urllib3.exceptions.NewConnectionError:
        print_error("NewConnectionError in " + process_name)
    except urllib3.exceptions.MaxRetryError:
        print_error("MaxRetryError in " + process_name)
    except requests.exceptions.ConnectionError:
        print_error("ConnectionError in " + process_name)
    if response == None:
        return response
    return response


def update_values_post(iot_name, uri):
    response = None
    try:
        request = requests.post(uri)
        data_json = request.text
        response = json.loads(data_json)
    except requests.exceptions.HTTPError:
        print_error("HTTPError in " + iot_name)
    except ConnectionRefusedError:
        print_error("ConnectionRefusedError in " + iot_name)
    except urllib3.exceptions.NewConnectionError:
        print_error("NewConnectionError in " + iot_name)
    except urllib3.exceptions.MaxRetryError:
        print_error("MaxRetryError in " + iot_name)
    except requests.exceptions.ConnectionError:
        print_error("ConnectionError in " + iot_name)

    if response == None:
        return response
    return response


def print_error(error):
    print('\n' + Fore.RED + error)
    send_error_email(error)


def send_error_email(message):
    config = get_config()
    subject = "Error in IoT Building" + config['storage']['local']['database']
    to_email = "rdpds@isep.ipp.pt"

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "noreplytiocps@gmail.com"
    smtp_password = "T!ocpsGecad2023"

    # Create a MIMEText object to represent the email message
    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach the message to the email
    msg.attach(MIMEText(message, 'plain'))

    # Establish a connection to the SMTP server
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
    except Exception as e:
        print(f"Error: Unable to connect to the SMTP server - {e}")
        return

    # Send the email
    try:
        server.sendmail(smtp_username, to_email, msg.as_string())
        print("Email sent successfully")
    except Exception as e:
        print(f"Error: Unable to send the email - {e}")
    finally:
        server.quit()
