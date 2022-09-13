import json
import csv
import os
import argparse
from falconpy.hosts import Hosts

def create_file(name, ext):
    import datetime
    d = datetime.datetime.today()
    d_formatdate = d.strftime('%m-%d-%Y-%I-%M-%S')
    filename = name + "_" + d_formatdate + "." + ext
    import os
    f = open(filename, "x")
    f.close()
    return filename


def device_list(off: int, limit: int):
    """Return a list of all devices for the CID, paginating when necessary."""
    result = falcon.query_devices_by_filter_scroll(limit=limit, offset=off)
    new_offset = 0
    total = 0
    returned_device_list = []
    if result["status_code"] == 200:
        new_offset = result["body"]["meta"]["pagination"]["offset"]
        total = result["body"]["meta"]["pagination"]["total"]
        returned_device_list = result["body"]["resources"]

    return new_offset, total, returned_device_list

def device_detail(aids: list):
    """Return the device_id and agent_version for a list of AIDs provided."""
    result = falcon.get_device_details(ids=aids)
    device_details = []
    if result["status_code"] == 200:
        # return just the aid and agent version
        for device in result["body"]["resources"]:
            res = {}
            res["hostname"] = device.get("hostname", None)
            res["product_type_desc"] = device.get("product_type_desc", None)
            res["platform_name"] = device.get("platform_name", None)
            res["os_version"] = device.get("os_version", None)
            res["local_ip"] = device.get("local_ip", None)
            res["mac_address"] = device.get("mac_address", None)
            res["machine_domain"] = device.get("machine_domain", None)
            res["last_seen"] = device.get("last_seen", None)
            res["agent_version"] = device.get("agent_version", None)
            res["update_pol_id"] = device["device_policies"].get("sensor_update", {}).get("policy_id", None)
            res["rfm"] = device.get("reduced_functionality_mode", None)
            device_details.append(res)
    return device_details

# Local variable:
report_file = create_file("export_cs", "csv")

# Grab our config parameters from a local file.
with open('./config.json', 'r') as file_config:
    config = json.loads(file_config.read())


falcon = Hosts(creds={
        "client_id": config["falcon_client_id"],
        "client_secret": config["falcon_client_secret"]
    },
     base_url = "https://api.eu-1.crowdstrike.com"   # Enter your base URL here if it is not US-1
)

OFFSET = None   # First time the token is null
DISPLAYED = 0   # Running count
TOTAL = 1       # Assume there is at least one
LIMIT = 500     # Quick limit to prove pagination
all_devices = []  # All devices retrieved
offset_pos = 0  # Start at the beginning
while offset_pos < TOTAL:
    OFFSET, TOTAL, devices = device_list(OFFSET, LIMIT)
    offset_pos += LIMIT
    details = device_detail(devices)
    for detail in details:
        DISPLAYED += 1
        all_devices.append([detail['hostname'], detail['product_type_desc'], detail['platform_name'], detail['os_version'], detail['local_ip'], detail['mac_address'], detail['machine_domain'], detail['last_seen'], detail['agent_version'], detail['update_pol_id'], detail['rfm']])


if not DISPLAYED:
    print("No results returned.")

# Generate a CSV from our results
with open(report_file, "w") as file_handle:
    for device in all_devices:
        file_handle.write(f"{device[0]},{device[1]},{device[2]},{device[3]},{device[4]},{device[5]},{device[6]},{device[7]},{device[8]},{device[9]},{device[10]}\n")
