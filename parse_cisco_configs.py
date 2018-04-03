#!/usr/local/bin/python3

"""
Parse Cisco router configs for vlans and addresses
"""

import argparse
import csv
import ipaddress
import os
import re
import sys


def parse_vlans(config, site, device):
    """
    Example config section:
        interface TenGigabitEthernet6/5
         description rtr-example-xe-0-3-6
         ip address 198.51.100.1 255.255.255.254
         ipv6 address 2001:db8:dead::beef/127
        !
        interface Vlan60
         description another-example
         ip address 192.0.2.1 255.255.255.192
         ipv6 address 2001:db8:beef:dead::1/64
        !
    """
    # setup regex
    re_vid = re.compile(r'^\s*interface Vlan(?P<vid>\d+)$')
    #re_interface = re.compile(r'^\s*interface (?P<interface>(Loopback|FastEthernet|GigabitEthernet|TenGigabitEthernet)[0-9/]+)$')
    re_desc = re.compile(r'^\s*description (?P<desc>[\w./-]+)$')
    re_ipv4 = re.compile(r'^\s*ip address (?P<address>[0-9.]+) (?P<netmask>[0-9.]+)$')
    re_ipv6 = re.compile(r'^\s*ipv6 address (?P<address>[0-9A-Fa-f:/]+)$')
    re_end = re.compile(r'^\s*!$')
    re_blank = re.compile(r'^\s*$')

    # flag if in vlan block
    vlan_block = False

    # create empty dict for scoping issues
    vlan = dict()
    vlans = list()
    for line in config:
        # skip blank lines
        if re_blank.match(line):
            continue

        # reset vlan block flag and continue
        if re_end.match(line):
            vlan_block = False
            continue

        # check if opening new unit block
        if re_vid.match(line):
            # set flag that we've entered a vlan block
            vlan_block = True
            # in a new unit block, pull out vlan id
            vid = re_vid.match(line).group('vid')
            name = '{device}-v{vid}'.format(
                device=device,
                vid=vid,
            )
            # store known information in new dict
            vlan = {
                'site': site.upper(),
                'group_name': device,
                'vid': vid,
                'name': name,
                'tenant': '',
                'status': 'Active',
                'role': '',
            }
            # add new dict to list
            vlans.append(vlan)

        # only want to check the following when in a vlan block
        if vlan_block:
            # check if setting description
            if re_desc.match(line):
                vlan['description'] = re_desc.match(line).group('desc')
            # check if setting address
            elif re_ipv4.match(line):
                address = re_ipv4.match(line).group('address')
                netmask = re_ipv4.match(line).group('netmask')
                try:
                    ip_info = ipaddress.ip_interface(
                        '{address}/{netmask}'.format(
                            address=address,
                            netmask=netmask,
                        )
                    )
                    vlan['ipv4_network'] = str(ip_info.network)
                    vlan['ipv4_gateway'] = ip_info.with_prefixlen
                except ValueError as e:
                    print(
                        'Exception converting {address}/{netmask} to IP'.format(
                            address=address,
                            netmask=netmask,
                        )
                    )
                    sys.exit(str(e))
            elif re_ipv6.match(line):
                address = re_ipv6.match(line).group('address')
                try:
                    ip_info = ipaddress.ip_interface(address)
                    vlan['ipv6_network'] = str(ip_info.network)
                    vlan['ipv6_gateway'] = ip_info.with_prefixlen
                except ValueError as e:
                    print('Exception converting {address} to IP'.format(address=address))
                    sys.exit(str(e))
    return vlans


def write_vlans(vlans, site, device, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = [
            'site',
            'group_name',
            'vid',
            'name',
            'tenant',
            'status',
            'role',
            'description',
            'ipv4_network',
            'ipv4_gateway',
            'ipv6_network',
            'ipv6_gateway',
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect='unix')
        writer.writeheader()
        writer.writerows(vlans)


def main():
    parser = argparse.ArgumentParser(
        description='Parse Cisco router config for vlans and addresses',
    )
    parser.add_argument(
        '-i',
        '--input_file',
        type=str,
        default='routers.txt',
        help='file containing devices to poll',
    )
    parser.add_argument(
        '-o',
        '--output_file',
        type=str,
        default='routers_vlans.csv',
        help='location for output file ',
    )
    parser.add_argument(
        'site',
        type=str,
        help='Netbox site',
    )
    parser.add_argument(
        'device',
        type=str,
        help='name of device',
    )
    args = parser.parse_args()

    lines = list()
    with open(args.input_file, 'r') as infile:
        lines = infile.readlines()
    if len(lines) == 0:
        sys.exit(
            'Unable to read {input_file} or {input_file} is empty'.format(
                input_file=args.input_file,
            )
        )

    vlans = parse_vlans(lines, args.site, args.device)
    write_vlans(vlans, args.site, args.device, args.output_file)


if __name__ == '__main__':
    main()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
