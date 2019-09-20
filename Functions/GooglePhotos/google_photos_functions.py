import json
import requests
from google.oauth2.credentials import Credentials

credentials_file = 'credentials.json'
clientID_file = 'client_id.json'

def uploadPicture(credentials, file, albumId, picture_name):
    f = open(file, 'rb').read()
    url = 'https://photoslibrary.googleapis.com/v1/uploads'
    headers = {
        'Authorization': "Bearer " + credentials.token,
        'Content-Type': 'application/octet-stream',
        'X-Goog-Upload-File-Name': file,
        'X-Goog-Upload-Protocol': "raw",
    }
    r = requests.post(url, data=f, headers=headers)
    upload_token = str(r.content, 'utf-8')
    #return upload_token

#def createItem(credentials, upload_token, albumId, picture_name):
    url = 'https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate'
    body = {
        'newMediaItems': [
            {
                "description": picture_name,
                "simpleMediaItem": {
                    "uploadToken": upload_token
                }
            }
        ]
    }
    if albumId is not None:
        body['albumId'] = albumId
    bodySerialized = json.dumps(body)
    headers = {
        'Authorization': "Bearer " + credentials.token,
        'Content-Type': 'application/json',
    }
    r = requests.post(url, data=bodySerialized, headers=headers)
    jsn = ''.join(str(x, 'utf-8') for x in r.content.split())
    creation_info = json.loads(jsn)
    status = creation_info['newMediaItemResults'][0]['status']['message']
    #print('status: '+str(status))
    if status == 'Success':
        result = True
        print('Succesfull uploaded ' + picture_name )
    else:
        result = False
        print('Failed to upload ' + picture_name )
    return result

def create_album(credentials, album_name):
    print('Create new album')
    url_create = 'https://photoslibrary.googleapis.com/v1/albums'
    headers = {
        'Authorization': "Bearer " + credentials.token,
        'Content-Type': 'application/json',
    }
    body_create = {
        "album":
            {
                "title": album_name
            }
    }
    body_create_Serialized = json.dumps(body_create)
    r = requests.post(url_create, data=body_create_Serialized, headers=headers)
    jsn = ''.join(str(x,'utf-8' ) for x in r.content.split())
    Album_info = json.loads(jsn)
    albumId = Album_info['id']

    url_share = 'https://photoslibrary.googleapis.com/v1/albums/' + albumId + ':share'
    body_share = {
        "sharedAlbumOptions": {
            "isCollaborative": False,
            "isCommentable": False
        }
    }
    body_share_Serialized = json.dumps(body_share)
    r = requests.post(url_share, data=body_share_Serialized, headers=headers)
    jsn = ''.join(str(x, 'utf-8') for x in r.content.split())
    share_info = json.loads(jsn)

    albumTitle = Album_info['title']
    albumUrl = share_info['shareInfo']['shareableUrl']
    print('New album created ')
    print('Name: ', albumTitle)
    print('ID: ', albumId)
    print('Sharable URL: ', albumUrl)
    return albumId, albumUrl

def Save_Credentials(Creds):
    credentials_file = './Functions/GooglePhotos_final/credentials.json'
    credentials_data = []
    credentials_data.append(Creds.client_id)
    credentials_data.append(Creds.client_secret)
    credentials_data.append(Creds.id_token)
    credentials_data.append(Creds.refresh_token)
    credentials_data.append(Creds.scopes)
    credentials_data.append(Creds.token_uri)
    with open(credentials_file, 'w') as f:
        json.dump(credentials_data, f)
    print('Credentials saved')

def Get_Credentials():
    try:
        credentials_file = './Functions/GooglePhotos_final/credentials.json'
        with open(credentials_file, 'r') as f:
            data = json.load(f)
        client_id = data[0]
        client_secret = data[1]
        id_token = data[2]
        refresh_token = data[3]
        scopes = data[4]
        token_uri = data[5]
        Creds = Credentials(None, refresh_token, id_token, token_uri, client_id, client_secret, scopes)
        Creds.refresh
        print('successfull retrieved credentials from file')
        result = True
    except:
        Creds = Credentials
        print('failed to retrieved credentials from file')
        result = False
    return Creds, result


