#!/usr/bin/env python3

import csv
import ipaddress
import sys


def unique_addresses():
    netbox_list = set()
    with open('ipplan_addresses.csv', newline='') as ipplan_csv, open('netbox_ipam_ipaddress.csv', newline='') as netbox_csv, open('unique_addresses.csv', 'w', newline='') as outfile:
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

        netbox = csv.DictReader(netbox_csv)
        for address in netbox:
            ip = ipaddress.ip_interface(address['address'])
            netbox_list.add(str(ip))

        ipplan = csv.DictReader(ipplan_csv)
        for address in ipplan:
            ip = ipaddress.ip_interface(address['address'])
            print('Processing {ip}'.format(ip=ip))
            if str(ip) not in netbox_list:
                writer.writerow(address)


def main():
    unique_addresses()


if __name__ == '__main__':
    main()


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
