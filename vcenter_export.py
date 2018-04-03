#!/usr/bin/env python3

"""
Process vCenter export for hostnames and IPs
"""

import argparse
import csv
import ipaddress
import os
import re
import sys


def parse_vms(vms, site, input_file):
    #fieldnames = [
    #    'Name',
    #    'State',
    #    'Guest OS',
    #    'DNS Name',
    #    'VM Storage Policies Compliance',
    #    'Status',
    #    'Managed By',
    #    'Host',
    #    'Host Type',
    #    'Provisioned Space',
    #    'Used Space',
    #    'Host CPU',
    #    'Host Mem',
    #    'Guest Mem - %',
    #    'Compatibility',
    #    'Memory Size',
    #    'Reservation',
    #    'CPUs',
    #    'NICs',
    #    'Uptime',
    #    'IP Address',
    #    'VMware Tools Version Status',
    #    'VMware Tools Running Status',
    #    'EVC Mode',
    #    'UUID',
    #    'Notes',
    #    'Alarm Actions',
    #    'HA Protection',
    #    'Needs Consolidation',
    #    'Encryption',
    #    'Datacenter',
    #    'Cluster',
    #    'Shares Value',
    #    'Limit - IOPs',
    #    'Datastore % Shares',
    #]

    vm_list = list()
    with open(input_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile, dialect='unix')

        for vm in reader:
            print(
                vm['Name'],
                vm['State'],
                vm['Guest OS'],
                vm['DNS Name'],
                vm['Provisioned Space'],
                vm['Memory Size'],
                vm['CPUs'],
                vm['IP Address'],
                vm['Cluster'],
            )
            print()


def write_vms(vms, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = [
            'name',
            'status',
            'cluster',
            'role',
            'tenant',
            'platform',
            'vcpus',
            'memory',
            'disk',
            'comments',
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect='unix')
        writer.writeheader()
        writer.writerows(vms)


def main():
    parser = argparse.ArgumentParser(
        description='Parse vCenter export for hostnames and addresses',
    )
    parser.add_argument(
        'input_file',
        type=str,
        help='file containing vCenter export',
    )
    parser.add_argument(
        'output_file',
        type=str,
        help='location for output file ',
    )
    parser.add_argument(
        'site',
        type=str,
        help='Netbox site',
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

    vms = parse_vms(lines, args.site, args.input_file)
    #write_vms(vms, args.output_file)


if __name__ == '__main__':
    main()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
