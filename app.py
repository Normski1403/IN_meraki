#!/usr/bin/python3
''' Script to poll the VF IN network dashboard for data
'''
import meraki
import json


def main():
    dashboard = meraki.DashboardAPI()
    my_orgs = dashboard.organizations.getOrganizations()
    org_id = my_orgs[0]['id']
    print(org_id)
    print(json.dumps(my_orgs, indent=4))
    print('================================')
    


if __name__ == '__main__':
    main()
