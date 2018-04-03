#!/usr/bin/env python3

import csv
import sys


def unique_vlans():
    netbox_list = set()
    with open('ipplan_vlans.csv', newline='') as ipplan_csv, open('netbox_vlans.csv', newline='') as netbox_csv, open('unique_vlans.csv', 'w', newline='') as outfile:
        # setup header for csv file
        fieldnames = [
            'site',
            'group_name',
            'vid',
            'name',
            'tenant',
            'status',
            'role',
            'description',
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, dialect='unix')
        writer.writeheader()

        netbox = csv.DictReader(netbox_csv, dialect='unix', delimiter=',', quotechar='"')
        for vlan in netbox:
            net = '{group_name}-v{vid}'.format(group_name=vlan['group_name'], vid=vlan['vid']).lower()
            netbox_list.add(net)

        ipplan = csv.DictReader(ipplan_csv, dialect='unix', delimiter=',', quotechar='"')
        for vlan in ipplan:
            ip = '{group_name}-v{vid}'.format(group_name=vlan['group_name'], vid=vlan['vid']).lower()
            if ip not in netbox_list:
                writer.writerow(vlan)


def unique_prefixes():
    netbox_list = set()
    with open('ipplan_prefixes.csv', newline='') as ipplan_csv, open('netbox_prefixes.csv', newline='') as netbox_csv, open('unique_prefixes.csv', 'w', newline='') as outfile:
        # setup header for csv file
        fieldnames = [
            'prefix',
            'vrf',
            'tenant',
            'site',
            'vlan_group',
            'vlan_vid',
            'status',
            'role',
            'is_pool',
            'description',
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, dialect='unix')
        writer.writeheader()

        netbox = csv.DictReader(netbox_csv, dialect='unix', delimiter=',', quotechar='"')
        for prefix in netbox:
            netbox_list.add(prefix['prefix'])

        ipplan = csv.DictReader(ipplan_csv, dialect='unix', delimiter=',', quotechar='"')
        for prefix in ipplan:
            if prefix['prefix'] not in netbox_list:
                writer.writerow(prefix)


def unique_addresses():
    netbox_list = set()
    with open('ipplan_addresses.csv', newline='') as ipplan_csv, open('netbox_addresses.csv', newline='') as netbox_csv, open('unique_addresses.csv', 'w', newline='') as outfile:
        # setup header for csv file
        fieldnames = [
            'address',
            'vrf',
            'tenant',
            'status',
            'role',
            'device',
            'virtual_machine',
            'interface_name',
            'is_primary',
            'description',
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, dialect='unix')
        writer.writeheader()

        netbox = csv.DictReader(netbox_csv, dialect='unix', delimiter=',', quotechar='"')
        for address in netbox:
            netbox_list.add(address['address'])

        ipplan = csv.DictReader(ipplan_csv, dialect='unix', delimiter=',', quotechar='"')
        for address in ipplan:
            if address['address'] not in netbox_list:
                writer.writerow(address)


def main():
    unique_vlans()
    unique_prefixes()
    unique_addresses()


if __name__ == '__main__':
    main()


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
