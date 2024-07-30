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
        print(f"[DEBUG] no body in event, maybe AWS EventBridge invoke the lambda")
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
    print(f"[DEBUG] try to get menu list from google spreadsheets")
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    print(f"[DEBUG] values: {values}")
    # Select a random menu
    menus = []
    for row in values:
        print(f"[DEBUG] row: {row}")
        menus.append(row[0])
    print(f"[INFO] menus: {menus}")
    selected_menu = random.choice(menus).strip()
    print(f"[INFO] selected_menu: {selected_menu}")
    # Send the selected menu to slack
    slack_message = {
        'text': f"오늘의 메뉴 추천은 {selected_menu}입니다!"
    }
    requests.post(response_url, data=json.dumps(slack_message), headers={'Content-Type': 'application/json'})
    # Return the response
    return {
        'statusCode': 200,
        'body': json.dumps(f'Message sent to Slack!\nMessage Content\n{slack_message}')
    }
    
