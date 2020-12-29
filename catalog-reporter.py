#!/usr/bin/env python3
import plistlib, sys, getopt, subprocess, json, urllib.request
from os import path, makedirs, listdir, remove
from shutil import copyfile
from time import sleep
from urllib.parse import urlparse

""" FUNCTIONS """
def compare_catalogs(base_catalog: list[dict], additonals_catalog: list[dict]) -> list[dict]:
    changed_software = []
    for additonal_software in additonals_catalog:
        software_has_changed = True
        for base_software in base_catalog:
            if additonal_software['name'] == base_software['name'] and additonal_software['version'] == base_software['version']:
                software_has_changed = False
                break
        
        if software_has_changed:
            changed_software.append(additonal_software)
    return changed_software

def convert_to_teams_section(software: dict, icon_url: str, skip_catalog_info: bool = False) -> dict:
    # Check if custom icon_name
    if icon_url:
        try: icon_name = software['icon_name']
        except: icon_name = software['name'] + ".png"
    
    # Check if display_name is given
    try: name = software['display_name']
    except: name = software['name']

    if software['catalogs'] and not skip_catalog_info: activityText = "Currently available in **" + ', '.join(software['catalogs']) + "**"
    elif not software['catalogs'] and skip_catalog_info: activityText = ""
    else: activityText = "Currently not available in any catalog"

    return {
        "activityImage": (app_icon_url.strip('/') + "/" + icon_name),
        "activityTitle": "**" + name + "**",
        "activitySubtitle": software['version'],
        "activityText": activityText
    }

def convert_list_to_teams_sections(software: list, icon_url: str, skip_catalog_info: bool = False) -> list:
    sections = []
    for item in software:
        sections.append(convert_to_teams_section(item, icon_url, skip_catalog_info))
    return sections

def replace_software_catalog_info(software: dict, catalog: list[dict]):
    for entry in catalog:
        if software['name'] == entry['name'] and software['version'] == entry['version']:
            software['catalogs'] = entry['catalogs']
            return software 
    software['catalogs'] = None
    return software

def send_teams_message(summary: str, sections: list[dict], webhook: str) -> str:
    data = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": summary,
        "sections": sections
    }

    data=json.dumps(data).encode('ascii')
    req = urllib.request.Request(url = webhook, headers = {'Content-Length': len(data), 'Content-Type': 'application/json; charset=ascii'})

    try:
        with urllib.request.urlopen(req, data) as response:
            return response.read().decode()
    except urllib.error.HTTPError as e: 
        return e.read().decode()

""" LOGIC """
# Init empty variables.
munki_repo: str
old_catalogs_base_dir: str
teams_webhook: str
app_icon_url: str
changed_data: dict

# Parse commandline arguments
help_message="""Usage: software_watcher.py [-m | --munki-repo <path-to-repo>] [-c | --catalog-cache-store <path-to-catalog-cache>] [-t | --teams-webhook] [-i | --icon-url]

All parameters are optional. If non are specified it simply runs and prints info to stdout.

munki-repo: Define the local path to the base directory of the munki repo. Defaults to munkiimport repo_url.
catalog-cache-store: Define a local path to a folder where to store the catalog copies to.
teams-webhook: If specified all reports are additionally sent to a teams webhook url.
icon-url: If specified webhook notifications will be enhanced with icons. [eg: https://myicons.com] This script will append the icon names of the software (munki) to the URL. [eg: https://myicons.com/GoogleChrome.png]
"""
try:
    opts, args = getopt.getopt(sys.argv[1:],"c:m:ht:i:",["munki-repo=","help","catalog-cache-store=","teams-webhook=","icon-url="])
except getopt.GetoptError as e:
    print("Unknown parameter "+e.opt)
    print(help_message)
    exit(2)
for opt, arg in opts:
    if opt in ("h", "--help"):
        print(help_message)
        sys.exit()
    elif opt in ("-m", "--munki-repo"):
        print("Set munki repo to " + arg)
        munki_repo = arg
    elif opt in ("-c", "--catalog-cache-store"):
        print("Set catalog cache store to " + arg)
        old_catalogs_base_dir = arg
    elif opt in ("-t", "--teams-webhook"):
        print("Notification will be sent to Teams")
        teams_webhook = arg
    elif opt in ("-i", "--icon-url"):
        print("Will send teams message with image")
        icon_url = arg



# Build variables from input
# Get repo from munkiimport config if not specified via parameter.
if not munki_repo:
    print("No munki repo path given. Trying reading configuration from munki")
    munki_repo = urlparse(subprocess.run(['/usr/bin/defaults', 'read', 'com.googlecode.munki.munkiimport', 'repo_url'], stdout=subprocess.PIPE).stdout.decode().rstrip()).path
    if not munki_repo:
        print("Key repo_url not configured in preference object com.github.autopkg. Alternativly user parameter --munki-repo", file = sys.stderr)
        exit(1)
if not path.exists(munki_repo):
    print("Path " + munki_repo + " was not found. [Hint: Tool only supports local repositories]")

new_catalogs_base_dir=path.join(munki_repo, "catalogs")
if not old_catalogs_base_dir:
    old_catalogs_base_dir=path.join(munki_repo, "catalog_report_cache")


# Check if required folders are there.
if not path.exists(new_catalogs_base_dir):
    print('Did not find path "' + new_catalogs_base_dir + '"', file = sys.stderr)
    exit(1)
if not path.exists(old_catalogs_base_dir):
    print("Creating directory to store previous catalog data in.")
    makedirs(old_catalogs_base_dir)



# Remove old catalog copys
for catalog_name in listdir(old_catalogs_base_dir):
    # Path to the catalog data
    new_catalog_path = path.join(new_catalogs_base_dir, catalog_name)
    old_catalog_path = path.join(old_catalogs_base_dir, catalog_name)

    if not path.exists(new_catalog_path):
        print("Tracking of " + catalog_name + "is not required anymore. Deleting copy.")
        remove(old_catalog_path)



# Process all catalogs.
with open(path.join(new_catalogs_base_dir, "all"), 'rb') as fp:
    all_catalog_data = plistlib.load(fp)

for catalog_name in listdir(new_catalogs_base_dir):
    # Skip if it is catalog all or hidden files
    if catalog_name == "all" or catalog_name.startswith(".") :
        continue

    # Path to the catalog data
    new_catalog_path = path.join(new_catalogs_base_dir, catalog_name)
    old_catalog_path = path.join(old_catalogs_base_dir, catalog_name)

    # Load catalog data.
    try:
        with open(new_catalog_path, 'rb') as fp:
            new_catalog_data = plistlib.load(fp)
    except plistlib.InvalidFileException:
        print("Skipping file " + new_catalog_path + " because it is not a valid catalog.", file=sys.stderr)
        continue
    with open(old_catalog_path, 'rb') as fp:
        old_catalog_data = plistlib.load(fp)

    # Make copy of current catalog if we have no old data.
    if not path.exists(old_catalog_path):
        print("New catalog detected. Creating copy of " + catalog_name)
        copyfile(new_catalog_path, old_catalog_path)
        continue

    # Compare data 
    changed_data[catalog_name] = {"new": [],"removed": []}
    changed_data[catalog_name]['new'] = compare_catalogs(old_catalog_data, new_catalog_data)
    changed_data[catalog_name]['removed'] = compare_catalogs(new_catalog_data, old_catalog_data)

    # Replace info in removed data so that software info represented correctly.
    for idx, item in enumerate(changed_data[catalog_name]['removed']):
        changed_data[catalog_name]['removed'][idx] = replace_software_catalog_info(changed_data[catalog_name]['removed'][idx], all_catalog_data)

    # Update the comparison cache catalogs
    if changed_data[catalog_name]['new'] or changed_data[catalog_name]['removed']:
        copyfile(new_catalog_path, old_catalog_path)



# Fill sections with new software
for catalog in changed_data.keys():
    teams_sections = []
    if changed_data[catalog]['new']:
        print(changed_data[catalog]['new'])
        teams_sections.append({"title": "Software has been **added** to catalog **" + catalog + "**:"})
        teams_sections += convert_list_to_teams_sections(changed_data[catalog]['new'], app_icon_url)
        if teams_webhook:
            send_teams_message("New software added to Munki", teams_sections, teams_webhook)
    teams_sections = []
    if changed_data[catalog]['removed']:
        print(changed_data[catalog]['removed'])
        teams_sections.append({"title": "Software has been **removed** from catalog **" + catalog + "**:"})
        teams_sections += convert_list_to_teams_sections(changed_data[catalog]['removed'], app_icon_url)
        if teams_webhook:
            send_teams_message("New software added to Munki", teams_sections, teams_webhook)