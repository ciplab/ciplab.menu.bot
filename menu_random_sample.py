import os
import logging
import boto3
import random
import json
import requests
import urllib.parse
import urllib.request
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build


def lambda_handler(event, context):
    if 'body' in event:
        logging.info("The slash command invoke lambda")
        # Response to the slack
        body = urllib.parse.parse_qs(event['body'])
        logging.debug(f"body: {body}")
        response_url = body.get('response_url', None)[0]
        assert response_url is not None, "The response_url is not in the body"
        requests.post(response_url, data=json.dumps({
            'text': "처리 중 입니다. :alarm_clock:"
        }), headers={'Content-Type': 'application/json'})
        # Queue to SQS
        SQS = boto3.client('sqs')
        SQS.send_message(
            QueueUrl=os.getenv("SQS_QUERY_URL"),
            MessageBody=event['body']
        )
        return {
            'statusCode': 200,
            'body': json.dumps('The query is queued to SQS')
        }
    # Load environment variables
    load_dotenv()
    DEFAULT_RESPONSE_URL = os.getenv("DEFAULT_RESPONSE_URL")
    SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    RANGE_NAME = os.getenv("RANGE_NAME")
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    if 'Records' in event:
        logging.info("SQS invoke the lambda")
        body = urllib.parse.parse_qs(event['Records'][0]['body'])
        logging.debug(f"body: {body}")
        response_url = body.get('response_url', DEFAULT_RESPONSE_URL)[0]
        category = body.get('text', [''])[0]
    else:
        logging.info(f"no body in event, maybe AWS EventBridge invoke the lambda")
        response_url = DEFAULT_RESPONSE_URL
        category = ''
    logging.info(f"response_url: {response_url}")
    logging.info(f"category: {category}")
    # Get the menu list from google spreadsheets
    logging.info("try to get menu list from google spreadsheets")
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    # Filter with category
    if category != '':
        new_values = []
        for row in values:
            if category in row[1]:
                new_values.append(row)
        values = new_values
    # Prepare menus, probs
    menus = []
    probs = []
    for row in values:
        menus.append(row[0])
        if row[2].isdigit():
            probs.append(int(row[2]))
        else:
            probs.append(1)
    probs = [p / sum(probs) for p in probs]
    logging.info(f"[INFO] menus: {menus}")
    logging.info(f"[INFO] probs: {probs}")
    # Random sample menus and generate slack message
    if len(menus) == 0:
        slack_message = "조건에 맞는 메뉴가 없습니다. CIPLAB_menu_list를 확인하거나 학식이나 먹으러 가시죠 :ciplab_party:"
    else:
        emoji_map = [':one:', ':two:', ':three:', ':four:', ':five:', ':six:', ':seven:', ':eight:', ':nine:']
        selected_menu = random.sample(menus, min(5, len(menus)))
        logging.info(f"[INFO] selected_menu: {selected_menu}")
        slack_message = f"오늘의 메뉴 추천은 "
        for i, sm in enumerate(selected_menu):
            if i == 0:
                slack_message += f"{emoji_map[i]} {sm}"
            else:
                slack_message += f", {emoji_map[i]} {sm}"
        slack_message += "입니다!\n이모지를 눌러 투표해주세요. :ciplab_party2:"
    # Send message to slack
    requests.post(response_url, data=json.dumps({
        'text': slack_message
    }), headers={'Content-Type': 'application/json'})
    # Return the response
    return {
        'statusCode': 200,
        'body': json.dumps('The selected menu is sent to Slack!')
    }
    
