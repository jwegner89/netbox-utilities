#!/usr/bin/python3.6

"""
Parse router configs for vlans
"""

import argparse
import csv
import getpass
import ipaddress
import json
import netmiko
import os
import re
import socket
import sys


def pull_config(device, user, password):
    try:
        # retrieve IP from hostname
        ip = socket.gethostbyname(device)
        conn_info = {
            'device_type': 'juniper_junos',
            'ip': ip,
            'username': user,
            'password': password,
        }

        net_connect = netmiko.ConnectHandler(**conn_info)
        # at some point, vlans became irbs, so try both and concatenate them
        irbs = net_connect.send_command('show configuration interfaces irb')
        vlans = net_connect.send_command('show configuration interfaces vlan')
        return irbs + vlans

    except socket.gaierror as e:
        print('Device {device} is not resolvable.'.format(device=device))
        sys.exit(str(e))


def parse_vlans(device, config):
    """
    Example Juniper config section:
    unit 91 {
        description rtr-example-servers;
        family inet {
            ... snip ...
            address 203.0.113.1/27;
        }
        family inet6 {
            ... snip ...
            address 2001:db8:beef:feed::1/64;
        }
    }
    """
    # setup regex
    re_site = re.compile(r'(mfc|rtr)-(?P<site>\w+)-\w+')
    re_vid = re.compile(r'^\s*unit (?P<vid>\d+) {$')
    re_desc = re.compile(r'^\s*description (?P<desc>[\w-]+);$')
    re_address = re.compile(r'^\s*address (?P<address>[0-9A-Fa-f:/.]+);$')
    re_blank = re.compile(r'^\s*$')

    # parse site
    site = ''
    group_name = device.split('.')[0]
    site_match = re_site.match(group_name)
    if site_match:
        site = site_match.group('site')
    if len(site) == 0:
        sys.exit('Unable to parse site for {group_name}'.format(group_name=group_name))

    # create empty dict for scoping issues
    vlan = dict()
    vlans = list()
    for line in config.split('\n'):
        # skip blank lines
        if re_blank.match(line):
            continue

        # check if opening new unit block
        if re_vid.match(line):
            # in a new unit block, pull out vlan id
            vid = re_vid.match(line).group('vid')
            name = '{group_name}-v{vid}'.format(
                group_name=group_name,
                vid=vid,
            )
            # store known information in new dict
            vlan = {
                'site': site.upper(),
                'group_name': group_name,
                'vid': vid,
                'name': name,
                'tenant': '',
                'status': 'Active',
                'role': '',
            }
            # add new dict to list
            vlans.append(vlan)
        # check if setting description
        elif re_desc.match(line):
            vlan['description'] = re_desc.match(line).group('desc')
        # check if setting address
        elif re_address.match(line):
            address = re_address.match(line).group('address')
            try:
                ip_info = ipaddress.ip_interface(address)
                if isinstance(ip_info, ipaddress.IPv4Interface):
                    vlan['ipv4_network'] = str(ip_info.network)
                    vlan['ipv4_gateway'] = ip_info.with_prefixlen
                if isinstance(ip_info, ipaddress.IPv6Interface):
                    vlan['ipv6_network'] = str(ip_info.network)
                    vlan['ipv6_gateway'] = ip_info.with_prefixlen
            except ValueError as e:
                print('Exception converting {address} to IP'.format(address=address))
                sys.exit(str(e))
    return vlans


def write_vlans(vlans, output_file):
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
        description='Parse router configs for vlans',
    )
    parser.add_argument(
        '-u',
        '--user',
        type=str,
        default='admin',
        help='user for device login',
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
    args = parser.parse_args()

    devices = list()

    with open(args.input_file, 'r') as infile:
        devices = infile.readlines()

    if len(devices) == 0:
        sys.exit(
            'Unable to read {input_file} or {input_file} is empty'.format(
                input_file=args.input_file,
            )
        )

    password = getpass.getpass('Password for {user}: '.format(user=args.user))

    vlans = list()
    for device in devices:
        device = device.lower().strip()
        config = pull_config(device, args.user, password)
        vlans.extend(parse_vlans(device, config))
    write_vlans(vlans, args.output_file)


if __name__ == '__main__':
    main()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
