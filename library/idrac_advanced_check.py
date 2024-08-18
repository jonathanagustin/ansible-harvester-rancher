#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible module for performing advanced checks on iDRAC.

This module connects to an iDRAC interface and performs a series of checks
to ensure the system is ready for Harvester installation.
"""

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.redfish_utils import RedfishUtils

ANSIBLE_METADATA = {"metadata_version": "1.2", "status": ["preview"], "supported_by": "community"}

DOCUMENTATION = """
---
module: idrac_advanced_check
short_description: Perform advanced checks on iDRAC
description:
    - This module performs advanced checks on iDRAC to ensure it's ready for Harvester installation.
    - It verifies hardware compatibility, firmware versions, system health, and RAID configuration.
options:
    idrac_ip:
        description: iDRAC IP address
        required: true
        type: str
    idrac_user:
        description: iDRAC username
        required: true
        type: str
    idrac_password:
        description: iDRAC password
        required: true
        type: str
    min_firmware_version:
        description: Minimum required iDRAC firmware version
        required: false
        type: str
        default: "4.40.00.00"
    min_cpu_count:
        description: Minimum required CPU count
        required: false
        type: int
        default: 4
    min_memory_gb:
        description: Minimum required memory in GB
        required: false
        type: int
        default: 32
"""

EXAMPLES = """
- name: Perform advanced iDRAC checks
  idrac_advanced_check:
    idrac_ip: "{{ inventory_hostname }}"
    idrac_user: "{{ idrac_user }}"
    idrac_password: "{{ idrac_password }}"
    min_firmware_version: "4.50.00.00"
    min_cpu_count: 8
    min_memory_gb: 64
"""

RETURN = """
msg:
    description: Detailed message about the checks performed
    type: str
    returned: always
failed:
    description: Indicates if any checks failed
    type: bool
    returned: always
check_results:
    description: Detailed results of each check
    type: dict
    returned: always
"""


def check_firmware_version(idrac, min_version):
    """
    Check if the iDRAC firmware version is compatible.

    Args:
        idrac (RedfishUtils): The iDRAC connection object.
        min_version (str): Minimum required firmware version.

    Returns:
        tuple: (bool, str) indicating success/failure and a message.
    """
    try:
        firmware_version = idrac.get_firmware_version()
        if re.match(r"^\d+\.\d+\.\d+\.\d+$", firmware_version):
            if firmware_version >= min_version:
                return True, f"Firmware version {firmware_version} is compatible"
            else:
                return False, f"Firmware version {firmware_version} is below the minimum required version {min_version}"
        else:
            return False, f"Invalid firmware version format: {firmware_version}"
    except Exception as e:
        return False, f"Error checking firmware version: {str(e)}"


def check_hardware_compatibility(idrac, min_cpu_count, min_memory_gb):
    """
    Check if the hardware is compatible with Harvester.

    Args:
        idrac (RedfishUtils): The iDRAC connection object.
        min_cpu_count (int): Minimum required CPU count.
        min_memory_gb (int): Minimum required memory in GB.

    Returns:
        tuple: (bool, str) indicating success/failure and a message.
    """
    try:
        system_info = idrac.get_system_info()

        cpu_count = system_info.get("ProcessorSummary", {}).get("Count", 0)
        memory_gb = system_info.get("MemorySummary", {}).get("TotalSystemMemoryGiB", 0)

        if cpu_count < min_cpu_count or memory_gb < min_memory_gb:
            return False, f"Hardware does not meet minimum requirements. CPUs: {cpu_count}/{min_cpu_count}, RAM: {memory_gb}/{min_memory_gb}GB"

        return True, f"Hardware meets minimum requirements. CPUs: {cpu_count}, RAM: {memory_gb}GB"
    except Exception as e:
        return False, f"Error checking hardware compatibility: {str(e)}"


def check_system_health(idrac):
    """
    Check overall system health.

    Args:
        idrac (RedfishUtils): The iDRAC connection object.

    Returns:
        tuple: (bool, str) indicating success/failure and a message.
    """
    try:
        health_info = idrac.get_system_health()

        if health_info.get("Status", {}).get("Health") == "OK":
            return True, "System health is good"
        else:
            return False, f"System health is not OK: {health_info.get('Status', {}).get('Health')}"
    except Exception as e:
        return False, f"Error checking system health: {str(e)}"


def check_raid_configuration(idrac):
    """
    Check RAID configuration.

    Args:
        idrac (RedfishUtils): The iDRAC connection object.

    Returns:
        tuple: (bool, str) indicating success/failure and a message.
    """
    try:
        raid_info = idrac.get_raid_controller_info()

        if not raid_info:
            return False, "No RAID controllers found"

        for controller in raid_info:
            if controller.get("Status", {}).get("Health") != "OK":
                return False, f"RAID controller {controller.get('Id')} health is not OK"

        return True, "RAID configuration is healthy"
    except Exception as e:
        return False, f"Error checking RAID configuration: {str(e)}"


def run_module():
    """
    Main function to run the Ansible module.
    """
    module_args = dict(
        idrac_ip=dict(required=True, type="str"),
        idrac_user=dict(required=True, type="str"),
        idrac_password=dict(required=True, type="str", no_log=True),
        min_firmware_version=dict(required=False, type="str", default="4.40.00.00"),
        min_cpu_count=dict(required=False, type="int", default=4),
        min_memory_gb=dict(required=False, type="int", default=32),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Initialize iDRAC connection
        idrac = RedfishUtils(creds=dict(ip=module.params["idrac_ip"], username=module.params["idrac_user"], password=module.params["idrac_password"]), root_uri="/redfish/v1", timeout=30)

        # Perform advanced checks
        checks = [(check_firmware_version, [module.params["min_firmware_version"]]), (check_hardware_compatibility, [module.params["min_cpu_count"], module.params["min_memory_gb"]]), (check_system_health, []), (check_raid_configuration, [])]

        failed_checks = []
        check_results = {}
        for check, args in checks:
            success, message = check(idrac, *args)
            check_name = check.__name__
            check_results[check_name] = {"success": success, "message": message}
            if not success:
                failed_checks.append(message)

        # Prepare result
        result = dict(changed=False, msg="Advanced iDRAC checks completed", failed=bool(failed_checks), check_results=check_results)

        if failed_checks:
            result["msg"] = f"Advanced iDRAC checks failed: {', '.join(failed_checks)}"
        else:
            result["msg"] = "All advanced iDRAC checks passed successfully"

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f"An error occurred during iDRAC checks: {str(e)}")


if __name__ == "__main__":
    run_module()
