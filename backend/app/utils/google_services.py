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

