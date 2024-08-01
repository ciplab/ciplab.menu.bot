import random
import json
import requests
import urllib.parse
import urllib.request
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build


# Load environment variables
load_dotenv()
DEFAULT_RESPONSE_URL = os.getenv("DEFAULT_RESPONSE_URL")

SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
RANGE_NAME = os.getenv("RANGE_NAME")
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def lambda_handler(event, context):
    # # DEBUG for internet access
    # import requests
    # try:
    #     response = requests.get("https://httpbin.org/ip")
    #     return {
    #         'statusCode': 200,
    #         'body': json.dumps({
    #             'message': 'Success',
    #             'response': response.json()
    #         })
    #     }
    # except requests.exceptions.RequestException as e:
    #     return {
    #         'statusCode': 500,
    #         'body': json.dumps({
    #             'message': 'Failed to connect',
    #             'error': str(e)
    #         })
    #     }
    # Get the slack api response_url from the event
    print(f"[DEBUG] event: {event}")
    print(f"[DEBUG] context: {context}")
    if 'body' in event:
        body = urllib.parse.parse_qs(event['body'])
        print(f"[DEBUG] body: {body}")
        response_url = body.get('response_url', DEFAULT_RESPONSE_URL)[0]
        print(f"[INFO] response_url: {response_url}")
    else:
        print(f"[INFO] no body in event, maybe AWS EventBridge invoke the lambda")
        response_url = DEFAULT_RESPONSE_URL
        print(f"[INFO] response_url: {response_url}")
    # # DEBUG for reading service account file
    # def read_and_print_service_account_file(file_path):
    #     try:
    #         with open(file_path, 'r') as file:
    #             content = file.read()
    #             print("File content:")
    #             print(content)
    #     except Exception as e:
    #         print(f"Failed to read the file: {str(e)}")
    # read_and_print_service_account_file(SERVICE_ACCOUNT_FILE)
    # Get the menu list from google spreadsheets
    print(f"[INFO] try to get menu list from google spreadsheets")
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    # print(f"[DEBUG] values: {values}")
    # Filter with category
    category = body.get('text', '')[0]
    print(f"[INFO] category: {category}")
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
        # print(f"[DEBUG] row: {row}")
        menus.append(row[0])
        if row[2].isdigit():
            probs.append(int(row[2]))
        else:
            probs.append(1)
    probs = [p / sum(probs) for p in probs]
    print(f"[INFO] menus: {menus}")
    print(f"[INFO] probs: {probs}")
    # Random sample menus and generate slack message
    if len(menus) == 0:
        slack_message = "조건에 맞는 메뉴가 없습니다. CIPLAB_menu_list를 확인하거나 학식이나 먹으러 가시죠 :ciplab_party:"
    else:
        emoji_map = [':one:', ':two:', ':three:', ':four:', ':five:', ':six:', ':seven:', ':eight:', ':nine:']
        selected_menu = random.sample(menus, min(5, len(menus)))
        print(f"[INFO] selected_menu: {selected_menu}")
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
        'body': json.dumps(f'Message sent to Slack!\nMessage Content\n{slack_message}')
    }
    
