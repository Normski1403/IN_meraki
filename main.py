#!/usr/bin/python3
''' Script to poll the VF IN network dashboard for data
'''
import meraki
import json
from datetime import datetime, timedelta


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
    total, upload, download = 0,0,0
    for client in response:
        total += client['usage']['total']
        upload += client['usage']['sent']
        download += client['usage']['recv']
        # print(f"{client['mac']}  Total: {total}  Upload: {upload}   Download: {download}")
    return total, upload, download


def getOrganizationNetworks(id):
    ''' List all of the devices with the organisation, this will contain the following which are
    required for follow up API calls:
        - name
        - networkID # Used to get usage statistics
    '''
    networks_api = dashboard.organizations.getOrganizationNetworks(
                                        id, total_pages='all', tagsFilterType="withAllTags"
                                        )
    networks = []
    for device in networks_api:
        network = {}
        network['name'] = device.get('name')
        network['id'] = device.get('id')
        if len(device.get('tags')) > 0:
            network['tag'] = device.get('tags')[0]
        else:
            network['tag'] = "No tag"
        network['total clients'], network['avg of clients'] = getNetworkClientOverview(device['id'])
        network['total'], network['upload'], network['download'] = getNetworkClients(device['id'])
        print(json.dumps(network, indent=4))
        networks.append(network)


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
    

def main():
    global dashboard
    now = datetime.now()
    getSeconds(now)
    dashboard = meraki.DashboardAPI(log_path='logging/', print_console=False)
    my_orgs = dashboard.organizations.getOrganizations()
    org_id = my_orgs[0]['id']
    print(org_id)
    print('================================')
    getOrganizationNetworks(org_id)


if __name__ == '__main__':
    main()