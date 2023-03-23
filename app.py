#!/usr/bin/python3
''' Script to poll the VF IN network dashboard for data
'''
import meraki


def main():
    dashboard = meraki.DashboardAPI()
    my_orgs = dashboard.organizations.getOrganizations()
    print(my_orgs)


if __name__ == '__main__':
    main()
