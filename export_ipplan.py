#!/usr/bin/env python3

import argparse
import csv
import ipaddress
import math
import operator
import re
import sys


def parse_prefixes(sql):
    values = list()

    for line in sql:
        if 'INSERT INTO `base`' == line[:18]:
            # line is of form
            # INSERT INTO `base` VALUES (...),...,(...);\n
            line = line[27:-3]
            values.extend(line.split('),('))

    if not values:
        sys.exit('Error: cannot convert SQL to CSV')

    # use csv module to convert SQL inserts
    fieldnames = [
        'baseaddr',
        'subnetsize',
        'descrip',
        'baseindex',
        'admingrp',
        'customer',
        'lastmod',
        'userid',
        'swipmod',
        'baseopt',
    ]
    reader = csv.DictReader(
        values,
        fieldnames=fieldnames,
        dialect='unix',
        delimiter=',',
        quotechar="'",
    )

    # regex to match vlans if present
    re_vlan = re.compile(r'(?P<group>(mfc|rtr)-\w+-\w+)-v(?P<vlan>\d+) : (?P<desc>.*)')
    re_info = re.compile(r'(mfc|rtr)-(?P<site>\w+)-(?P<loc>\w+)')

    vlans = list()
    prefixes = list()

    for row in reader:
        # subnetsize given in available IPs for subnet, e.g. 256, 512
        # so we need to convert it to its corresponding CIDR mask
        mask = 32 - int(math.log(int(row['subnetsize']), 2))
        addr_from_int = str(ipaddress.ip_address(int(row['baseaddr'])))
        network = '{network}/{mask}'.format(network=addr_from_int, mask=mask)
        descrip = row['descrip'].strip()
        prefix = {
            'prefix': network,
            'vrf': '',
            'tenant': '',
            'site': '',
            'vlan_group': '',
            'vlan_vid': '',
            'status': 'Active',
            'role': '',
            'is_pool': 'false',
            'description': descrip,
        }
        prefixes.append(prefix)
        vlan_match = re_vlan.match(descrip)
        info_match = re_info.match(descrip)
        if vlan_match:
            vlan_group = vlan_match.group('group')
            vlan_vid = vlan_match.group('vlan')
            desc = vlan_match.group('desc')
            info_match = re_info.match(vlan_group)
            site = info_match.group('site')
            loc = info_match.group('loc')
            vlan_desc = desc.lower().replace(' ', '-')
            prefix['site'] = site.upper()
            prefix['vlan_group'] = vlan_group
            prefix['vlan_vid'] = vlan_vid
            prefix['description'] = desc
            vlan = {
                'site': site.upper(),
                'group_name': vlan_group,
                'vid': vlan_vid,
                'name': desc,
                'tenant': '',
                'status': 'Active',
                'role': '',
                'description': '',
            }
            vlans.append(vlan)
        elif info_match:
            info_match = re_info.match(vlan_group)
            site = info_match.group('site')
            loc = info_match.group('loc')
            vlan_desc = descrip.lower().replace(' ', '-')
            prefix['site'] = site.upper()
            prefix['vlan_group'] = vlan_group
            prefix['vlan_vid'] = vlan_vid
            prefix['description'] = descrip
            vlan = {
                'site': site.upper(),
                'group_name': vlan_group,
                'vid': vlan_vid,
                'name': descrip,
                'tenant': '',
                'status': 'Active',
                'role': '',
                'description': '',
            }
            vlans.append(vlan)

    # sort lists according to vlan ID for easy comparison
    prefixes = sorted(prefixes, key=operator.itemgetter('vlan_vid'))
    vlans = sorted(vlans, key=operator.itemgetter('vid'))

    with open('ipplan_prefixes.csv', 'w', newline='') as csvfile:
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
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect='unix')
        writer.writeheader()
        writer.writerows(prefixes)

    with open('ipplan_vlans.csv', 'w', newline='') as csvfile:
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
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect='unix')
        writer.writeheader()
        writer.writerows(vlans)


def parse_addresses(sql):
    values = list()

    for line in sql:
        if 'INSERT INTO `ipaddr`' == line[:20]:
            # line is of form
            # INSERT INTO `ipaddr` VALUES (...),...,(...);\n
            line = line[29:-3]
            values.extend(line.split('),('))

    if not values:
        sys.exit('Error: cannot convert SQL to CSV')

    # use csv module to convert from SQL
    fieldnames = [
        'ipaddr',
        'userinf',
        'location',
        'telno',
        'descrip',
        'baseindex',
        'lastmod',
        'userid',
        'hname',
        'macaddr',
        'lastpol',
    ]
    reader = csv.DictReader(
        values,
        fieldnames=fieldnames,
        dialect='unix',
        delimiter=',',
        quotechar="'",
    )

    # create list to store IP dictionaries
    ips = list()

    for row in reader:
        desc = row['descrip'].strip()
        name = row['hname'].strip()
        description = ''
        if name and not desc:
            description = name
        elif desc and not name:
            if desc != 'Unknown - added by IPplan command line poller':
                description = desc
        elif desc and name:
            if desc == name or desc == 'Unknown - added by IPplan command line poller':
                description = name
            else:
                description = '{} - {}'.format(name, desc)
        address = str(ipaddress.ip_address(int(row['ipaddr']))) + '/32'
        ip = {
            'address': address,
            'status': 'Active',
            'description': description,
        }
        ips.append(ip)

    with open('ipplan_addresses.csv', 'w', newline='') as csvfile:
        fieldnames = [
            'address',
            'status',
            'description',
        ]
        ips = sorted(ips, key=operator.itemgetter('address'))
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
            dialect='unix',
        )
        writer.writeheader()
        writer.writerows(ips)


def main():
    parser = argparse.ArgumentParser(
        description='generate CSV for Netbox import for IPPlan MySQL dump',
    )
    parser.add_argument(
        'input',
        type=str,
        help='MySQL dump file for import',
    )
    args = parser.parse_args()

    sql = ''
    with open(args.input, 'r') as infile:
        sql = infile.readlines()

    if not sql:
        sys.exit('Error reading input file')

    parse_prefixes(sql)
    parse_addresses(sql)


if __name__ == '__main__':
    main()


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
