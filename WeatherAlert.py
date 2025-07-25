
import json
import requests
import boto3
from botocore.exceptions import ClientError

# Clients
secrets_client = boto3.client('secretsmanager')
sns_client = boto3.client('sns')

# Configuration
LOCATION = "Andhra Pradesh,IN"
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:934860271554:WeatherAlertsTopic"
FORCE_TEST_ALERT = True  # Set to True to force SMS for testing

def get_api_key():
    secret_name = "WeatherNotifierSecrets"
    secret = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(secret['SecretString'])['weatherApiKey']

def get_weather(api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={LOCATION}&units=imperial&appid={api_key}"
    response = requests.get(url)
    return response.json()

def is_alert_condition(data):
    weather = data['weather'][0]['main'].lower()
    temp = data['main']['temp']
    if 'rain' in weather or 'snow' in weather:
        return True
    if temp < 32 or temp > 95:
        return True
    return False

def send_sms(message):
    print(f"📤 Attempting to send SMS: {message}")
    response = sns_client.publish(TopicArn=SNS_TOPIC_ARN, Message=message)
    print("📨 SNS Publish Response:", response)

def lambda_handler(event, context):
    try:
        api_key = get_api_key()
        data = get_weather(api_key)

        # Debug log
        print("🔍 Weather API response:", json.dumps(data, indent=2))

        if FORCE_TEST_ALERT or is_alert_condition(data):
            condition = data['weather'][0]['description']
            temp = data['main']['temp']
            msg = f"⚠ Weather Alert!\nCondition: {condition}\nTemperature: {temp}°F"
            send_sms(msg)
            return {"statusCode": 200, "body": "SMS alert sent"}
        else:
            return {"statusCode": 200, "body": "No alert needed"}

    except ClientError as e:
        return {"statusCode": 500, "body": str(e)}
    except Exception as e:
        return {"statusCode": 500, "body": f"Unexpected error: {str(e)}"}
