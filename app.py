#!/usr/bin/python3
''' Script to poll the VF IN network dashboard for data
'''
import meraki
import json
from datetime import datetime
import calendar
import argparse


def getNetworkClientOverview(network_id):
    ''' Gets the stats for a particular site.
    '''
    response = dashboard.networks.getNetworkClientsOverview(network_id)
    print(json.dumps(response, indent=4))


def getOrganistaionDevices(id):
    ''' List all of the devices with the organisation, this will contain the following which are
    required for follow up API calls:
        - name
        - networkID # Used to get usage statistics
        - serial number # 
    '''
    all_devices = dashboard.organizations.getOrganizationDevicesStatuses(id, total_pages='all')
    print(json.dumps(all_devices, indent=4))
    for device in all_devices:
        #print(f"{device['name']} - {device['networkId']} - {device['tags']}")
        getNetworkClientOverview(device['networkId'])


def getOrganizationNetworks(id):
    ''' List all of the devices with the organisation, this will contain the following which are
    required for follow up API calls:
        - name
        - networkID # Used to get usage statistics
    '''
    response = dashboard.organizations.getOrganizationNetworks(
                                        id, total_pages='all', tagsFilterType="withAllTags"
                                        )
    for device in response:
        print(f"{device['name']} - {device['id']} - {device['tags']}")
        getNetworkClientOverview(device['id'])


def getOrganisationClientOverview(id):
    ''' This will collect all stats for the last 7 days at an organisation level
    Use to define set data parameters
    t0 = 2023-03-10 00:00:00    t1 = 2023-03-16 23:59:59 
    '''
    client_data = dashboard.organizations.getOrganizationClientsOverview(id, timespan=604800)
    print(json.dumps(client_data, indent=4))


def getTimeSpan():
    ''' Takes the users selection or the current month and year and gets start and finish
    time in a datetime object.
    '''
    if args.month == 'Dec':
        year = args.year-1
    else:
        year = args.year
    # Convert 'Feb' into 2
    month = int(datetime.strptime(args.month, '%b').strftime('%m'))
    start_time = datetime(year, month, 1)
    last_day = int(calendar.monthrange(year, month)[1])
    end_time = datetime(year, month, last_day, 23, 59, 59)
    diff = now - end_time
    if diff.total_seconds() < 0:
        print('You have selected a month with incomplete data, please only select months that are completed')
        exit(1)
    return start_time, end_time


def main():
    start_time, end_time = getTimeSpan()
    global dashboard
    dashboard = meraki.DashboardAPI(log_path='logging/', print_console=False)
    my_orgs = dashboard.organizations.getOrganizations()
    org_id = my_orgs[0]['id']
    print(org_id)
    # print(json.dumps(my_orgs, indent=4))
    # print('================================')
    # getOrganistaionDevices(org_id)
    print('================================')
    getOrganizationNetworks(org_id)
    # getOrganisationClientOverview(org_id)


if __name__ == '__main__':
    global args, now
    now = datetime.now()
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("--month", help="Select the month", 
                                   choices=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 
                                   default=now.strftime('%b'))
    parser.add_argument("--year", help="Select the year", 
                                  type=int,
                                  default=now.year)
    args = parser.parse_args()
    main()
