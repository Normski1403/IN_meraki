#!/usr/bin/python3
''' Script to poll the VF IN network dashboard for data
'''
import meraki
import os
import json

from dotenv import load_dotenv
from datetime import datetime, timedelta
from pprint import pprint as pp

load_dotenv()


def calculate_time_range():
    global yesterday_start, yesterday_end, today

    # Get the current date
    today = datetime.now()
    yesterday = datetime.now() - timedelta(days=counter)
    
    # Set t1: 23:59 of the current day
    yesterday_end = yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
    
    # Set t0: Midnight of the first day of the same month
    yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

    # 31 day rolling 
    print(f"yesterday_start: {yesterday_start}")
    print(f"yesterday_end: {yesterday_end}")
    


def convert_kb_to_higher_unit(kilobytes):
    units = ["KB", "MB", "GB", "TB"]
    size = kilobytes
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"


def get_organisations():
    ''' Get the orgs in the meraki, UK and DE
    Sample output:
    {'api': {'enabled': True},
        'cloud': {'region': {'host': {'name': 'Europe'}, 'name': 'Europe'}},
        'id': '543462',
        'licensing': {'model': 'co-term'},
        'management': {'details': [{'name': 'customer number', 'value': '71145990'}]},
        'name': 'Vodafone Foundation',
        'url': 'https://n577.meraki.com/o/i0-kTd/manage/organization/overview'}
    '''
    my_orgs = dashboard.organizations.getOrganizations()
    return my_orgs


def getOrganizationNetworks(id):
    ''' List all of the devices with the organisation, this will contain the following which are
    required for follow up API calls:
        - name
        - networkID # Used to get usage statistics

    Sample output:
    {'enrollmentString': None,
     'id': 'N_3702521843651970977',
     'isBoundToConfigTemplate': False,
     'isVirtual': False,
     'name': 'A-ER-MINI-KIT_8_NL',
     'notes': None,
     'organizationId': '543462',
     'productTypes': ['appliance'],
     'tags': ['Valencia_Flood_24'],
     'timeZone': 'America/Los_Angeles',
     'url': 'https://n577.meraki.com/A-ER-MINI-KIT_8_/n/3_MbPbjxb/manage/clients'}
    '''
    networks_api = dashboard.organizations.getOrganizationNetworks(
                                        id, total_pages='all', tagsFilterType="withAllTags"
                                        )
    return networks_api
    

def getNetworkClientOverview(network_id):
    ''' Gets the stats for a particular site.
    {
    "counts": {
        "total": 86,
        "withHeavyUsage": 1
    },
    "usages": {
        "average": 1706457, ## This is in kilobytes
        "withHeavyUsageAverage": 31077896
    }
    }

    # USING ABOVE OUTPUT AS AN EXAMPLE
    86 * 1706457 = 146755302 KB
    1 GB = 1024 × 1024 KB = 1048576 KB
    
    146755302 KB ÷ 1048576 KB = 139.93 GB

    ### DASHBOARD ###
    Total Data Transferred
    139.94GB    

    '''
    response = dashboard.networks.getNetworkClientsOverview(network_id, 
                                                            resolution=7200, 
                                                            t0=yesterday_start, 
                                                            t1=yesterday_end)
    return response['counts']['total'], response['usages']['average']


def get_tags(network_tags):
    if len(network_tags) == 1:
        return network_tags[0]
    elif len(network_tags) > 1:
        return ",".join(network_tags)
    else:
        return "No tag"
    

def main():
    api_key = os.getenv("MERAKI_DASHBOARD_API_KEY")

    global dashboard
    now = datetime.now()
    dashboard = meraki.DashboardAPI(api_key, log_path='logging/', print_console=False)

    ''' Get the list of organistaions to get the ID's for the UK and DE instances '''
    my_orgs = get_organisations()

    ''' For each org, get a list of all the networks that are in it. This will return
    a list of all networks '''
    networks = []
    for org in my_orgs:
        org_id = org['id']
        networks.extend(getOrganizationNetworks(org_id))

    global counter
    counter = 31
    while counter > 0:
        calculate_time_range()
        ''' Using the list of networks '''
        all_network_data = []
        for network in networks:
            current_network = {}
            current_network['timestamp'] = yesterday_end.isoformat(timespec="seconds")
            current_network['name'] = network.get('name')
            current_network['id'] = network.get('id')
            current_network['organizationId'] = network.get('organizationId')
            current_network['tag'] = get_tags(network.get('tags'))
            current_network['total_clients'], current_network['avg_of_clients'] = getNetworkClientOverview(network['id'])
            if current_network['avg_of_clients'] == 0:
                # print(f"Skipping site {network['name']} as no clients detected...")
                continue
            # print(f'{network['name']:70} || {network['tags']} >>> {convert_kb_to_higher_unit(clients * user_avg)}')
            current_network['total'] = current_network['total_clients'] * current_network['avg_of_clients']
            current_network['human_total'] = convert_kb_to_higher_unit(current_network['total'])
            print("JSON::" + json.dumps(current_network))
        counter -= 1
        print("########")

if __name__ == '__main__':
    main()
        

