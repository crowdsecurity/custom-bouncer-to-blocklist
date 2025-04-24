#!/usr/bin/env -S uv run python3

import os
import sys
import json
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


## Todo: get those from command line
KEY = os.getenv('KEY') or "xxxxxxx"
BLOCKLIST_NAME = os.getenv('BLOCKLIST_NAME') or "xxxxxxx"

def api_key_auth(auth):
    try:
        client = Info(base_url=Server.production_server.value, auth=auth)
        response = client.get_info()
    except Exception as e:
        print(f"Error: {e}")
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

        print(f"IPs deleted to blocklist: {blocklist_id}")
        print(f"IPs: {ips}")
        return response
    except HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        print(f"Status code: {e.response.status_code}")
        print(f"Response content: {e.response.content}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
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

        print(f"IPs added to blocklist: {blocklist_id}")
        print(f"IPs: {ips}")
        return response
    except HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        print(f"Status code: {e.response.status_code}")
        print(f"Response content: {e.response.content}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
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
        print(f"Blocklist not found: {BLOCKLIST_NAME}")
        return None
    except HTTPStatusError as e:
        if e.response.status_code == 404:
            # Blocklist not found
            print("Blocklist not found")
            return None
        else:
            print(f"HTTP error occurred: {e}")
            print(f"Status code: {e.response.status_code}")
            print(f"Response content: {e.response.content}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
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
        print(f"Blocklist created: {BLOCKLIST_NAME}")
        return response.id
    except HTTPStatusError as e:
        if e.response.status_code == 409:
            # Blocklist already exists, fetch instead
            print(f"Blocklist already exists: {BLOCKLIST_NAME}")
            return get_blocklist(auth)
        else:
            print(f"HTTP error occurred: {e}")
            print(f"Status code: {e.response.status_code}")
            print(f"Response content: {e.response.content}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def handle_command(action, ip, expiration):

    if action not in ["add", "del"]:
        print("Action must be 'add' or 'del'")
        return
    if not ip:
        print("IP must be provided")
        return
    if not expiration:
        print("Expiration must be provided")
        return

    # Verify if the API key is set and valid
    if KEY is None:
        print("API key not set. Please set the KEY environment variable.")
        return
    if BLOCKLIST_NAME is None:
        print("Blocklist name not set. Please set the BLOCKLIST_NAME environment variable.")
        return

    auth = ApiKeyAuth(api_key=KEY)
    if action == "add":
        blocklist_id = create_blocklist(auth)
        if blocklist_id is None:
            print("Failed to create or fetch blocklist")
            return
        # Add IPs to blocklist
        ips = [ip]
        add_resp = add_ip_to_blocklist(auth, blocklist_id, ips)
        print("IPs added to blocklist successfully")
    elif action == "del":
        blocklist_id = get_blocklist(auth)
        if blocklist_id is None:
            print("Failed to fetch blocklist")
            return
        # Remove IPs from blocklist
        ips = [ip]
        del_resp = del_ip_from_blocklist(auth, blocklist_id, ips, expiration=expiration)
        print("IPs removed from blocklist successfully")

def main():
    for line in sys.stdin:
        command = line.strip()
        if command.lower() == 'exit':
            print("Exiting.")
            break
        # Process the command here
        print(f"Received command: {command}")
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