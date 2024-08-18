# Harvester Installation Role

This Ansible role automates the installation of Harvester on Dell servers using iPXE boot and iDRAC for management.

## Requirements

- Ansible 2.9 or higher
- Dell servers with iDRAC access
- Proper network configuration for PXE booting
- Harvester ISO and required files accessible

## Role Variables

Here are some of the most important variables used by this role. For a full list, see `defaults/main.yml`.

```yaml
# Harvester Version
pxe_harvester_version: "v1.3.1"

# Network Configuration
pxe_harvester_mgmt_interface: "eno1"
pxe_harvester_vip: ""  # Must be set by user
netmask: "255.255.255.0"
gateway: ""  # Must be set by user
dns_servers: "8.8.8.8,8.8.4.4"
ntp_servers: "0.pool.ntp.org,1.pool.ntp.org"

# Storage Configuration
pxe_harvester_osdisk: "/dev/sda"
pxe_harvester_datadisk: "/dev/sdb"

# iDRAC Configuration
dell_idrac_version_min: "4.40.00.00"
dell_power_profile: "MaxPerformance"

# System Requirements
min_cpu_count: 4
min_memory_gb: 32
min_disk_space_gb: 120
```

## Dependencies

This role depends on the following Ansible collections:

- community.general
- dellemc.openmanage
- containers.podman

## Example Playbook

```yaml
- hosts: dell_servers
  roles:
     - { role: harvester_install, pxe_harvester_vip: "10.0.0.10", gateway: "10.0.0.1" }
```

## Usage

1. Ensure all prerequisites are met (network configuration, iDRAC access, etc.)
2. Configure your inventory and set necessary variables
3. Run the playbook:

   ```bash
   ansible-playbook -i inventory site.yml
   ```

## Post-Installation

After installation, the role will:

1. Verify the Harvester cluster health
2. Configure additional storage and networking (if enabled)
3. Set up monitoring (if enabled)
4. Perform cleanup tasks

## Troubleshooting

If the installation fails, the role will attempt to:

1. Log detailed error information
2. Perform a rollback to restore the server to its pre-installation state
3. Send a notification (via email and Mattermost) about the failure

Check the Ansible log output and the server's iDRAC logs for more information on any failures.

## License

BSD-3-Clause
