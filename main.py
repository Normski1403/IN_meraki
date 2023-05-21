#!/usr/bin/python3
''' Script to poll the VF IN network dashboard for data
'''
import meraki
import json
import os
from datetime import datetime, timedelta
from time import sleep, time
from pprint import pprint


def getNetworkClientOverview(network_id):
    ''' Gets the stats for a particular site.
    '''
    response = dashboard.networks.getNetworkClientsOverview(network_id, timespan=total_secs)
    # print(json.dumps(response, indent=4))
    return response['counts']['total'], response['usages']['average']


def getNetworkClients(network_id):
    ''' Gets the stats for a particular site by looping through.
    '''
    response = dashboard.networks.getNetworkClients(network_id, total_pages=-1, timespan=total_secs)
    # print(json.dumps(response, indent=4))
    total, upload, download, client_list = 0, 0, 0, ''
    for client in response:
        total += client['usage']['total']
        upload += client['usage']['sent']
        download += client['usage']['recv']
        client_list += f"{client['mac']},"
        # print(f"{client['mac']}  Total: {total}  Upload: {upload}   Download: {download}")
    # print(client_list)
    return total, upload, download, client_list


def getNetworkClientsApplicationUsage(id, client_list, application_data):
    ''' Get network application breakdown
    '''
    # clients = '72:c3:e5:31:8f:a0,96:df:ef:d5:eb:8c,c6:1f:54:ea:f0:d6'
    client_list = ",".join(client_list)
    response = dashboard.networks.getNetworkClientsApplicationUsage(
                                    id, client_list, total_pages='all', timespan=total_secs)
    # print(json.dumps(response, indent=4))
    for client in response:
        for app in client['applicationUsage']:
            # print(app)
            if application_data.get(app['application']) is None:
                # print(f"Application {app['application']} not found, adding to dict")
                application_data[app['application']] = {}
                application_data[app['application']]['received'] = int(app['received'])
                application_data[app['application']]['sent'] = int(app['sent'])
            else:
                # print(f"Application {app['application']} found, ammending dict")
                application_data[app['application']]['received'] += int(app['received'])
                application_data[app['application']]['sent'] += int(app['sent'])
        # print(application_data)
    # print(application_data)
    return application_data
        


def getOrganizationNetworks(id, networks):
    ''' List all of the devices with the organisation, this will contain the following which are
    required for follow up API calls:
        - name
        - networkID # Used to get usage statistics
    '''
    networks_api = dashboard.organizations.getOrganizationNetworks(
                                        id, total_pages='all', tagsFilterType="withAllTags"
                                        )
    for device in networks_api:
        network, application_data = {}, {}
        network['name'] = device.get('name')
        network['id'] = device.get('id')
        if len(device.get('tags')) == 1:
            network['tag'] = device.get('tags')[0]
        elif len(device.get('tags')) > 1:
            network['tag'] = ",".join(device.get('tags'))
        else:
            network['tag'] = "No tag"
        network['total clients'], network['avg of clients'] = getNetworkClientOverview(device['id'])
        if network['total clients'] == 0:
            print(f"Skipping site {network['name']}")
            continue
        network['total'], network['upload'], network['download'], client_list = getNetworkClients(device['id'])
        step = 20
        client_list = client_list.split(',')
        for pos in range(0, len(client_list), step):
            # print(f"Clients {pos} to {pos+step}")
            application_data = getNetworkClientsApplicationUsage(device['id'], client_list[pos:pos+step], application_data)
        for app, items in application_data.items():
            # print(f"{app} - {items}")
            application_data[app]['total'] = items['received'] + items['sent']
        print(f"Successfully collected data for site {network['name']}")
        pprint(application_data)
        networks.append(network)
    return networks


def getSeconds(now):
    '''
    From the date its executed, works out the number of days in the month before and converts that into
    seconds ready for the dashboard queries.

    now(datetime): The datetime object on script execution
    '''
    yesterday = now - timedelta(days=1)
    seconds_in_day = 86400
    global total_secs
    total_secs = yesterday.day * seconds_in_day
    print(total_secs)
    

def main():
    st = time()
    api_key = os.getenv("MERAKI_DASHBOARD_API_KEY")
    # print(api_key)
    global dashboard
    now = datetime.now()
    getSeconds(now)
    dashboard = meraki.DashboardAPI(api_key, log_path='logging/', print_console=False)
    my_orgs = dashboard.organizations.getOrganizations()
    networks = []
    # print(json.dumps(my_orgs, indent=4))
    for org in my_orgs:
        org_id = org['id']
        # print(org_id)
        # print('================================')
        getOrganizationNetworks(org_id, networks)
    print(json.dumps(networks, indent=4))
    et = time()
    print(et-st)


if __name__ == '__main__':
    main()