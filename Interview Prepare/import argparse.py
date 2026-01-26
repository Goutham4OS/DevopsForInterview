import argparse 
import requests
parser = argparse.ArgumentParser(description="Fetch and display data from a public API.")
parser.add_argument('--url',type=str,required=true,help='The URL of the public API to fetch data from.')
parser.parse_args()
args = parser.parse_args()
try:
  response = requests.get(args.url,timeout=10)
  response.raise_for_status()
  if response.status_code == 200:
    print("service is healthy")
except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
    exit(1)

import requests
import argparse,os


def fecth_work_flow_status():
   fetch_token_from_env = os.getenv("GITHUB_TOKEN")
   header = {
       "Accept": "application/vnd.github.v3+json",
       "User-Agent": "workflow-status-checker",
       "authorization": f"bearor {fetch_token_from_env}"
   }
   requests.get(url="githuworkflowsstatus.com/api/status",timeout=5,headers=header)
    response.raise_for_status()
   