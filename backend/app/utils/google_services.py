import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from app.utils.get_secret import get_secret


def get_google_creds(secret_name, region_name):
    # Fetch Google credentials from AWS Secrets Manager
    google_creds = get_secret(secret_name, region_name)
    return google_creds


def get_gspread_client(google_creds):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
    client = gspread.authorize(creds)
    return client


def set_sheet_permissions(file_id, google_creds, user_email):
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, ["https://www.googleapis.com/auth/drive"])
    drive_service = build('drive', 'v3', credentials=creds)

    # Define the permission body
    permission_body = {
        'type': 'anyone',
        'role': 'reader'
    }

    # Insert new permission for anyone to view
    drive_service.permissions().create(
        fileId=file_id,
        body=permission_body,
    ).execute()

    # Define the permission body for the user
    user_permission_body = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': user_email
    }

    # Insert new permission for the user to edit
    drive_service.permissions().create(
        fileId=file_id,
        body=user_permission_body,
    ).execute()


def set_form_permissions(form_id, google_creds, user_email):
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, ["https://www.googleapis.com/auth/drive"])
    drive_service = build('drive', 'v3', credentials=creds)

    # Define the permission body for the user
    user_permission_body = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': user_email
    }

    # Insert new permission for the user to edit
    drive_service.permissions().create(
        fileId=form_id,
        body=user_permission_body,
    ).execute()


def create_google_sheet(title, google_creds, user_email):
    client = get_gspread_client(google_creds)
    sheet = client.create(title)
    set_sheet_permissions(sheet.id, google_creds, user_email)
    return sheet.id


def create_google_form(title, google_creds, user_email):
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, ["https://www.googleapis.com/auth/forms",
                                                                            "https://www.googleapis.com/auth/drive"])
    service = build('forms', 'v1', credentials=creds)

    # Step 1: Create the form with only the title
    form = {
        "info": {
            "title": title,
            "documentTitle": title
        }
    }
    created_form = service.forms().create(body=form).execute()
    set_form_permissions(created_form['formId'], google_creds, user_email)

    # Step 2: Use batchUpdate to add questions
    requests = [
        {
            "createItem": {
                "item": {
                    "title": "Game Name",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "textQuestion": {
                                "paragraph": False
                            }
                        }
                    }
                },
                "location": {
                    "index": 0
                }
            }
        },
        {
            "createItem": {
                "item": {
                    "title": "Tag Line",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "textQuestion": {
                                "paragraph": False
                            }
                        }
                    }
                },
                "location": {
                    "index": 1
                }
            }
        }
    ]

    batch_update_request = {
        "requests": requests
    }
    service.forms().batchUpdate(formId=created_form['formId'], body=batch_update_request).execute()

    return created_form['formId']


def delete_google_sheet(sheet_id, google_creds):
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, ["https://www.googleapis.com/auth/drive"])
    drive_service = build('drive', 'v3', credentials=creds)
    drive_service.files().delete(fileId=sheet_id).execute()


def delete_google_form(form_id, google_creds):
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, ["https://www.googleapis.com/auth/drive"])
    drive_service = build('drive', 'v3', credentials=creds)
    drive_service.files().delete(fileId=form_id).execute()


def get_form_responses(form_id, google_creds):
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, ["https://www.googleapis.com/auth/drive"])
    service = build('forms', 'v1', credentials=creds)

    # Fetch the form responses
    responses = service.forms().responses().list(formId=form_id).execute()

    return responses.get('responses', [])


def get_form_details(form_id, google_creds):
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, ["https://www.googleapis.com/auth/drive"])
    service = build('forms', 'v1', credentials=creds)

    # Fetch the form details
    form_details = service.forms().get(formId=form_id).execute()

    return form_details


def get_existing_data(sheet_id, google_creds):
    client = get_gspread_client(google_creds)
    sheet = client.open_by_key(sheet_id).worksheet('Sheet1')
    existing_data = sheet.get_all_records()
    return existing_data


def write_responses_to_sheet(sheet_id, responses, google_creds, question_map):
    client = get_gspread_client(google_creds)
    sheet = client.open_by_key(sheet_id).worksheet('Sheet1')

    # Fetch existing data
    existing_data = get_existing_data(sheet_id, google_creds)

    # Extract existing Game Name and Tag Line pairs
    existing_pairs = set((row['Game Name'], row['Tag Line']) for row in existing_data)

    # Assuming the first row contains headers and data starts from the second row
    start_row = len(existing_data) + 2

    for response in responses:
        game_name = ""
        tag_line = ""
        for question_id, answer in response['answers'].items():
            question_text = question_map.get(question_id, "Unknown Question")
            if question_text == "Game Name":
                game_name = answer['textAnswers']['answers'][0]['value']
            elif question_text == "Tag Line":
                tag_line = answer['textAnswers']['answers'][0]['value']

        # Check if the pair already exists
        if (game_name, tag_line) not in existing_pairs:
            # Append the new data to the sheet
            sheet.append_row([game_name, tag_line], table_range=f'A{start_row}:B{start_row}')
            start_row += 1

