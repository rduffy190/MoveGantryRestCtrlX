# This example retrieves an appdata archive from a Github repository, uploads it to a CtrlX OS system and applies the configuration.
import requests
import json

# Step 1: Download archive from remote repository
local_archive_path = 'RemoteArchive.zip' # Your archive name here
remote_repo_url = 'https://github.com/S-Gilk/CtrlX-AppData/raw/refs/heads/main/RemoteArchive.zip' # Your remote repo url
response = requests.get(remote_repo_url)
with open(local_archive_path, 'wb') as f:
    f.write(response.content)

# Step 2: Authenticate to CtrlX OS
ctrlX_IP_address = "127.0.0.1:8443" # Your IP address here
base_url = "https://" + ctrlX_IP_address

payload = json.dumps({
  "name": "boschrexroth", # Your ctrlX OS username here
  "password": "boschrexroth" # Your ctrlX OS password here
})
headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", base_url + "/identity-manager/api/v1/auth/token", headers=headers, data=payload, verify=False)
print(response.text)

access_token= "Bearer " + response.json()['access_token']

# Step 3: Authorize to CtrlX OS and upload configuration

CtrlXOS_archive_name = "RemoteArchive"

with open(local_archive_path, 'rb') as f:
       zip_file_bytes = f.read()

headers = {
  'Content-Type': 'application/octet-stream',
  'Authorization': access_token
}

response = requests.request("PUT", base_url + "/solutions/api/v1/solutions/DefaultSolution/configurations/" + CtrlXOS_archive_name + "/archive?dir=%2F", data=zip_file_bytes, headers=headers, verify=False)
print(response.text)

# Step 4: Authorize on CtrlX OS and load configuration to active app data

payload = json.dumps({
  "action": "load",
  "properties": {
    "configurationPath": "solutions/DefaultSolution/configurations/" + CtrlXOS_archive_name
  }
})
headers = {
  'Content-Type': 'application/json',
  'Authorization': access_token
}
response = requests.request("POST", base_url + "/solutions/api/v1/tasks", headers=headers, data=payload, verify=False)
print(response.text)