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
            # print(f"Skipping site {network['name']} as no clients detected...")
            continue
        # print(f"Collecting site {network['name']}...")
        network['total'], network['upload'], network['download'], client_list = getNetworkClients(device['id'])
        # step: The number of MAC's to get from client API call
        # count: The total amount of data to work out the % an app has used of total data transfer
        step, total = 30, 0
        client_list = client_list.split(',')
        '''
        Step through the client list in groups of step and get all the application data, add the dictionary of
        application data to application_data list
        '''
        # print(f"{len(client_list)} detected in the last month...")
        for pos in range(0, len(client_list), step):
            # print(f"Collecting clients {pos} to {pos+step}")
            application_data = getNetworkClientsApplicationUsage(device['id'], client_list[pos:pos+step], application_data)
        '''
        Step through each application and combine tx and rx to get a total data value and add it to dictionary
        Also keeps a running total of the total amount of data sent.
        '''
        for app, items in application_data.items():
            # print(f"{app} - {items}")
            application_data[app]['total'] = items['received'] + items['sent']
            total += application_data[app]['total']
        '''
        Add to each application the % of the total data they used
        '''
        for app in application_data:
            application_data[app]["percent of total"] = (application_data[app]['total'] / total) * 100
        ''' 
        Sort the applcation into rank order using the total data as the sort value
        '''
        sorted_application_data = sorted(application_data.items(), key=lambda x: x[1]['total'], reverse=True)
        # pprint(application_data)
        # print(f"Successfully collected data for site {network['name']}")
        # pprint(sorted_application_data[:10])
        network['application data'] = {}
        '''
        Loop through the top 10 applications and add it into the overall site dictionary with the key being its
        position in the top 10 rank
        '''
        for count, app_data in enumerate(sorted_application_data[:10], start=1):
            combined_app_data = app_data[1]
            combined_app_data['application'] = app_data[0]
            network['application data'][count] = combined_app_data
            # print(combined_app_data)
        network['timestamp'] = datetime.now().isoformat(timespec="seconds")
        print(json.dumps(network))
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
    # print(total_secs)
    

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
    # print(json.dumps(networks, indent=4))
    et = time()
    # print(et-st)


if __name__ == '__main__':
    main()