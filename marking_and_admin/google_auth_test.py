# import os

# from google_auth_oauthlib.flow import Flow

# with open("temp_spreadsheet_creds.json", "w", encoding="utf-8") as tsc:
#     tsc.write(os.getenv("SPREADSHEET_CREDS", ""))
# # Create the flow using the client secrets file from the Google API
# # Console.
# flow = Flow.from_client_secrets_file(
#     "temp_spreadsheet_creds.json",
#     scopes=["https://www.googleapis.com/auth/spreadsheets"],
#     redirect_uri="https://design-computing.github.io/",
# )

# # Tell the user to go to the authorization URL.
# auth_url, _ = flow.authorization_url(prompt="consent")

# print(f"Please go to this URL:\n\n{auth_url}\n")

# # The user will get an authorization code. This code is used to get the
# # access token.
# code = input("Enter the authorization code: ")
# flow.fetch_token(code=code)

# # You can use flow.credentials, or you can just get a requests session
# # using flow.authorized_session.
# session = flow.authorized_session()
# print(session.get("https://www.googleapis.com/userinfo/v2/me").json())


import os
import pprint

import google.oauth2.credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

pp = pprint.PrettyPrinter(indent=2)

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
with open("temp_spreadsheet_creds.json", "w", encoding="utf-8") as tsc:
    tsc.write(os.getenv("SPREADSHEET_CREDS", ""))
CLIENT_SECRETS_FILE = "temp_spreadsheet_creds.json"

# This access scope grants read-only access to the authenticated user's Drive
# account.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
API_SERVICE_NAME = "spreadsheets"
API_VERSION = "v4"


def get_authenticated_service():
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        SCOPES,
        redirect_uri="https://design-computing.github.io/",
    )
    credentials = flow.run_console()
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


def list_drive_files(service, **kwargs):
    results = service.files().list(**kwargs).execute()

    pp.pprint(results)


if __name__ == "__main__":
    # When running locally, disable OAuthlib's HTTPs verification. When
    # running in production *do not* leave this option enabled.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    service = get_authenticated_service()
    list_drive_files(service, orderBy="modifiedByMeTime desc", pageSize=5)
