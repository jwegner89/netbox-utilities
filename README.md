# netbox-utilities
Utilities for Netbox management

* duplicates.py - Compare CSV files from an IPPlan export with a Netbox export
* duplicates_ipam.py - Compare IPPlan and Netbox addresses for duplicates
* export_ipplan.py - Parse an IPPlan MySQL export and export a CSV for import into Netbox
* parse_cisco_configs.py - Parse Cisco router configs for IP and VLAN information
* pull_juniper_router_vlans.py - Poll Junipers routers for IP and VLAN information
* Sync-Netbox.ps1 - Synchronize VMware vCenter virtual machine inventory with Netbox
* vcenter_export.py - parse a basic vCenter VM export to import into Netbox
* Remove-LogFiles.ps1 - simple script to cleanup synchronization log files older than 1 week
* vCenter_Netbox_Log_Cleanup.xml - Windows scheduled task example for cleaning log files older than 1 week
* vCenter_Netbox_Sync.xml - Windows scheduled task example for running the Sync-Netbox script nightly
