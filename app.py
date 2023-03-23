#!/usr/bin/python3
''' Script to poll the VF IN network dashboard for data
'''
import meraki
import json


def getNetworkClientOverview(network_id):
    '''
    '''
    response = dashboard.networks.getNetworkClientsOverview(network_id)
    print(network_id)
    print(json.dumps(response, indent=4))


def getOrganistaionDevices(id):
    ''' List all of the devices with the organisation, this will contain the following which are
    required for follow up API calls:
        - name
        - networkID # Used to get usage statistics
        - serial number # 
    '''
    all_devices = dashboard.organizations.getOrganizationDevicesStatuses(id, total_pages='all')
    # print(json.dumps(all_devices, indent=4))
    for device in all_devices:
        getNetworkClientOverview(device['networkId'])


def getOrganisationClientOverview(id):
    ''' This will collect all stats for the last 7 days at an organisation level
    Use to define set data parameters
    t0 = 2023-03-10 00:00:00    t1 = 2023-03-16 23:59:59 
    '''
    client_data = dashboard.organizations.getOrganizationClientsOverview(id, timespan=604800)
    print(json.dumps(client_data, indent=4))


def main():
    global dashboard
    dashboard = meraki.DashboardAPI(log_path='logging/')
    my_orgs = dashboard.organizations.getOrganizations()
    org_id = my_orgs[0]['id']
    print(org_id)
    # print(json.dumps(my_orgs, indent=4))
    print('================================')
    getOrganistaionDevices(org_id)
    # getOrganisationClientOverview(org_id)


if __name__ == '__main__':
    main()
