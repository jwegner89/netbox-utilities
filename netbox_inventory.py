#!/usr/bin/env python3

"""
Generate Ansible inventory from Netbox
"""

import json
import requests
import socket


def resolve_host(hostname):
    """
    Attempts to find the fully-qualified domain name of the given hostname
    based on some hard-coded domain names that apply to your organization
    """
    # unify to lowercase
    hostname = hostname.lower()
    # selection of domain names to try
    domains = [
        '.atl.example.com',
        '.dfw.example.com',
        '.ord.example.com',
        '.jfk.example.com',
    ]

    if '.' in hostname:
        # assume name is fully qualified
        try:
            socket.gethostbyname(hostname)
        except:
            # name was not resolved, but can't try more domains
            pass
    else:
        short = hostname
        resolved = False
        for domain in domains:
            fqdn = short + domain
            try:
                socket.gethostbyname(fqdn)
                # no exception thrown, so name was resolved
                resolved = True
                hostname = fqdn
                # do not consider other domains
                break
            except:
                # name was not resolved
                pass

    return hostname


def retrieve_vms(base_url, headers, site):
    """
    Retrieve all of the VM objects at a given site in Netbox
    We only manage RHEL 6/7 host with Ansible, so adjust as needed
    """
    vms_path = '/virtualization/virtual-machines/?q=&site={site}&status=1&platform=red-hat-enterprise-linux-6-64-bit&platform=red-hat-enterprise-linux-7-64-bit&limit=0'.format(site=site)
    vms_response = requests.get(
        base_url + vms_path,
        headers=headers,
    )
    vms_json = vms_response.json()['results']
    vms = set()
    for vm in vms_json:
        if vm['role'] and vm['role']['name'] == 'Appliance':
            # skip appliances marked as RHEL
            continue
        name = vm['name']
        hostname = resolve_host(name)
        if '.' in hostname:
            vms.add(hostname)
    return vms


def retrieve_devices(base_url, headers, site):
    """
    Retrieve all of the physical devices at a given site
    We only manage RHEL 6/7 host with Ansible, so adjust as needed
    """
    devices_path = '/dcim/devices/?q=&site={site}&status=1&platform=red-hat-enterprise-linux-6-64-bit&platform=red-hat-enterprise-linux-7-64-bit&limit=0'.format(site=site)
    devices_response = requests.get(
        base_url + devices_path,
        headers=headers,
    )
    devices_json = devices_response.json()['results']
    devices = set()
    for device in devices_json:
        if device['device_role'] and device['device_role']['name'] == 'Appliance':
            # skip appliances marked as RHEL
            continue
        name = device['name']
        hostname = resolve_host(name)
        if '.' in hostname:
            devices.add(hostname)
    return devices


def filter_hosts(hosts, query):
    """
    Simple filter to group hosts by some basic criteria
    We do short acronyms for site and to designate production/test/etc
    """
    matches = set()
    for host in hosts:
        if query in host:
            matches.add(host)
    return matches


def print_hosts(outfile, hosts, environment):
    """
    Output the hosts according to a particular environment
    For example, one might be production and another might be testing
    """
    outfile.write('[{environment}]\n'.format(environment=environment))
    for host in sorted(hosts):
        outfile.write(host + '\n')
    outfile.write('\n')


def main():
    """
    Retrieves all devices and VMs from Netbox and sorts them into specified criteria
    which can be consumed as an Ansible inventory file
    """
    # setup basic requests portions
    # adjust URL for your instance
    base_url = 'https://netbox.example.com/api'
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Token your-token-here',
    }

    # corresponds to sites with physical devices
    # adjust to your site designations
    devices = {
        'atl': set(),
        'ord': set(),
        'jfk': set(),
        'dfw': set(),
    }

    # corresponds to sites with virtual machine clusters
    # adjust to your site designations
    vms = {
        'ord': set(),
        'jfk': set(),
    }

    sites = devices.keys()

    for site in devices.keys():
        devices[site] = retrieve_devices(base_url, headers, site)

    for site in vms.keys():
        vms[site] = retrieve_vms(base_url, headers, site)

    all_hosts = set()
    for device_set in devices.values():
        all_hosts |= device_set
    for vm_set in vms.values():
        all_hosts |= vm_set

    # we encode a hosts "environment" (e.g. production/testing) in the hostname
    # so we filter based on those matches
    test_hosts = filter_hosts(all_hosts, 'tst')
    dev_hosts = filter_hosts(all_hosts, 'dev')
    nonprd_hosts = test_hosts | dev_hosts
    # we assume that everything is production if it's not marked
    prd_hosts = all_hosts - nonprd_hosts

    # we output to ./hosts.netbox by default - sorry, I'll setup a fancier argparse sometime
    with open('hosts.netbox', 'w') as outfile:
        for site in sorted(sites):
            outfile.write('[{site}:children]\n{site}_physical\n'.format(site=site))
            if site in vms.keys():
                outfile.write('{site}_vms\n'.format(site=site))

            outfile.write('\n[{site}]\n\n'.format(site=site))

            outfile.write('[{site}_physical]\n'.format(site=site))
            for device in sorted(devices[site]):
                outfile.write(device + '\n')
            outfile.write('\n')

            if site in vms.keys():
                outfile.write('[{site}_vms]\n'.format(site=site))
                for vm in sorted(vms[site]):
                    outfile.write(vm + '\n')
                outfile.write('\n')
        
        # go through and output all groups
        print_hosts(outfile, test_hosts, 'testing')
        print_hosts(outfile, dev_hosts, 'development')
        print_hosts(outfile, nonprd_hosts, 'nonproduction')
        print_hosts(outfile, prd_hosts, 'production')


if __name__ == '__main__':
    main()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
