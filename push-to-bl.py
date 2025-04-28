import os
import sys
import json
import argparse
import re
from httpx import HTTPStatusError
from crowdsec_service_api import (
    Server,
    ApiKeyAuth,
    Blocklists,
    BlocklistCreateRequest,
    Info,
    BlocklistAddIPsRequest,
    BlocklistDeleteIPsRequest,
)

LOG_FILE = "/var/log/push2bl.log"

def log(message):
    print(message)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(message + "\n")
    except Exception as e:
        print(f"Failed to write to log file: {e}")

# Parse command line arguments
parser = argparse.ArgumentParser(description='CrowdSec bouncer to Service API blocklist')
parser.add_argument('--blocklist', dest='blocklist_name', 
                    help='Name of the blocklist ou want to feed (default: from env BLOCKLIST_NAME)')
parser.add_argument('--sapi-key', dest='api_key',
                    help='CrowdSec Service API key (default: from env SAPI_KEY)')
args = parser.parse_args()

# Configuration priority: command line args > environment variables > defaults
SAPI_KEY = args.api_key or os.getenv('SAPI_KEY')
BLOCKLIST_NAME = args.blocklist_name or os.getenv('BLOCKLIST_NAME')

if not SAPI_KEY:
    log("Error: No SAPI key provided. Use --sapi-key option or set SAPI_KEY environment variable.")
    sys.exit(1)

if not BLOCKLIST_NAME:
    log("Error: No blocklist name provided. Use --blocklist option or set BLOCKLIST_NAME environment variable.")
    sys.exit(1)

def api_key_auth(auth):
    try:
        client = Info(base_url=Server.production_server.value, auth=auth)
        response = client.get_info()
    except Exception as e:
        log(f"Error: {e}")
        return None
    return response

def del_ip_from_blocklist(auth, blocklist_id, ips, expiration=None):
    try:
        client = Blocklists(base_url=Server.production_server.value, auth=auth)

        request = BlocklistDeleteIPsRequest(
            ips=ips,
        )
        response = client.delete_ips_from_blocklist(
            request=request,
            blocklist_id=blocklist_id,
        )

        log(f"IPs deleted to blocklist: {blocklist_id}")
        log(f"IPs: {ips}")
        return response
    except HTTPStatusError as e:
        log(f"HTTP error occurred: {e}")
        log(f"Status code: {e.response.status_code}")
        log(f"Response content: {e.response.content}")
        return None
    except Exception as e:
        log(f"An error occurred: {e}")
        return None

def add_ip_to_blocklist(auth, blocklist_id, ips, expiration=None):
    try:
        client = Blocklists(base_url=Server.production_server.value, auth=auth)

        request = BlocklistAddIPsRequest(
            ips=ips,
            expiration=expiration,
        )
        response = client.add_ips_to_blocklist(
            request=request,
            blocklist_id=blocklist_id,
        )

        log(f"IPs added to blocklist: {blocklist_id}")
        log(f"IPs: {ips}")
        return response
    except HTTPStatusError as e:
        log(f"HTTP error occurred: {e}")
        log(f"Status code: {e.response.status_code}")
        log(f"Response content: {e.response.content}")
        return None
    except Exception as e:
        log(f"An error occurred: {e}")
        return None

def get_blocklist(auth):
    try:
        client = Blocklists(base_url=Server.production_server.value, auth=auth)

        response = client.get_blocklists(
            page=1,
            page_size=100,
            include_filter=["private"],
            size=50,
        )

        for blocklist in response.items:
            if BLOCKLIST_NAME == blocklist.name:
                print(f"Blocklist found: {BLOCKLIST_NAME}")
                return blocklist.id
        log(f"Blocklist not found: {BLOCKLIST_NAME}")
        return None
    except HTTPStatusError as e:
        if e.response.status_code == 404:
            # Blocklist not found
            log("Blocklist not found")
            return None
        else:
            log(f"HTTP error occurred: {e}")
            log(f"Status code: {e.response.status_code}")
            log(f"Response content: {e.response.content}")
            return None
    except Exception as e:
        log(f"An error occurred: {e}")
        return None

def parse_duration(duration_str):
    pattern = r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
    match = re.fullmatch(pattern, duration_str.strip())
    if not match:
        raise ValueError(f"Invalid duration format: {duration_str}")

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0

    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds

def create_blocklist(auth):
    try:
        client = Blocklists(base_url=Server.production_server.value, auth=auth)
        request = BlocklistCreateRequest(
                name=BLOCKLIST_NAME,
                label=None,
                description="Blocklist created by push2bl.py",
                references=None,
                tags=None,
        )
        response = client.create_blocklist(
            request=request,
        )
        log(f"Blocklist created: {BLOCKLIST_NAME}")
        return response.id
    except HTTPStatusError as e:
        if e.response.status_code == 409:
            # Blocklist already exists, fetch instead
            log(f"Blocklist already exists: {BLOCKLIST_NAME}")
            return get_blocklist(auth)
        else:
            log(f"HTTP error occurred: {e}")
            log(f"Status code: {e.response.status_code}")
            log(f"Response content: {e.response.content}")
            return None
    except Exception as e:
        log(f"An error occurred: {e}")
        return None


def handle_command(action, ip, expiration):

    if action not in ["add", "del"]:
        log("Action must be 'add' or 'del'")
        return
    if not ip:
        log("IP must be provided")
        return
    if not expiration:
        log("Expiration must be provided")
        return

    auth = ApiKeyAuth(api_key=SAPI_KEY)
    if action == "add":
        blocklist_id = create_blocklist(auth)
        if blocklist_id is None:
            log("Failed to create or fetch blocklist")
            return
        # Add IPs to blocklist
        ips = [ip]
        add_resp = add_ip_to_blocklist(auth, blocklist_id, ips)
        log("IPs added to blocklist successfully")
    elif action == "del":
        blocklist_id = get_blocklist(auth)
        if blocklist_id is None:
            log("Failed to fetch blocklist")
            return
        # Remove IPs from blocklist
        ips = [ip]
        del_resp = del_ip_from_blocklist(auth, blocklist_id, ips, expiration=expiration)
        log("IPs removed from blocklist successfully")

def main():
    log(f"Running push-to-bl.py with blocklist: {BLOCKLIST_NAME}")
    for line in sys.stdin:
        command = line.strip()
        log(f"Received command: {command}")
        if command.lower() == 'exit':
            log("Exiting.")
            break
        # Process the command here
        #{"duration":"3h59m51s","origin":"cscli","scenario":"manual 'ban' from '5cf8aff523424fa68e9335f28fec409aIfHabI3W9GsKHzab'","scope":"Ip","type":"ban","uuid":"6d287fea-2707-4a7c-a7f1-d94d1d1d6c13","value":"42.42.42.42","id":17371391,"action":"add"}
        obj = json.loads(command)
        if not obj:
            continue
        command = obj.get("action")
        ip = obj.get("value")
        expiration = parse_duration(obj.get("duration", "1h"))
        handle_command(command, ip, expiration)

if __name__ == "__main__":
    main()