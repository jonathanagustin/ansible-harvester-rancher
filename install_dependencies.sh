#!/bin/bash

# install_dependencies.sh
#
# This script installs all necessary dependencies for the Harvester installation playbook.
# It sets up Python, Ansible, and required Python packages.
#
# Usage: ./install_dependencies.sh
#
# Note: This script should be run with sudo privileges if not run as root.

# Exit immediately if a command exits with a non-zero status
set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install a package using apt-get
install_package() {
    echo "Installing $1..."
    sudo apt-get install -y "$1" || {
        echo "Failed to install $1. Please check your internet connection and try again."
        exit 1
    }
}

# Update package lists
echo "Updating package lists..."
sudo apt-get update -y || {
    echo "Failed to update package lists. Please check your internet connection and try again."
    exit 1
}

# Install Python 3 and pip if not already installed
if ! command_exists python3; then
    install_package python3
    install_package python3-pip
else
    echo "Python 3 and pip are already installed."
fi

# Create a virtual environment
echo "Creating a virtual environment..."
python3 -m venv harvester_venv || {
    echo "Failed to create virtual environment. Please ensure you have venv installed."
    exit 1
}

# Activate the virtual environment
echo "Activating virtual environment..."
source harvester_venv/bin/activate || {
    echo "Failed to activate virtual environment. Please check the harvester_venv directory."
    exit 1
}

# Upgrade pip within the virtual environment
echo "Upgrading pip..."
pip install --upgrade pip || {
    echo "Failed to upgrade pip. Please check your internet connection and try again."
    exit 1
}

# Install Ansible Core if not already installed
if ! command_exists ansible; then
    echo "Installing Ansible Core..."
    pip install "ansible-core>=2.17.2,<3.0.0" || {
        echo "Failed to install Ansible Core. Please check your internet connection and try again."
        exit 1
    }
else
    echo "Ansible is already installed. Checking version..."
    ansible_version=$(ansible --version | grep "core" | awk '{print $2}')
    if [[ "$(printf '%s\n' "2.17.2" "$ansible_version" | sort -V | head -n1)" != "2.17.2" ]]; then
        echo "Upgrading Ansible Core..."
        pip install --upgrade "ansible-core>=2.17.2,<3.0.0" || {
            echo "Failed to upgrade Ansible Core. Please check your internet connection and try again."
            exit 1
        }
    else
        echo "Ansible Core version is sufficient."
    fi
fi

# Install required Python packages
echo "Installing required Python packages..."
pip install -r requirements.txt || {
    echo "Failed to install required Python packages. Please check the requirements.txt file and your internet connection."
    exit 1
}

# Install required Ansible collections
echo "Installing required Ansible collections..."
ansible-galaxy collection install dellemc.openmanage containers.podman community.general || {
    echo "Failed to install required Ansible collections. Please check your internet connection and try again."
    exit 1
}

# Install additional packages in the virtual environment
echo "Installing additional packages in the virtual environment..."
pip install omsdk redfish || {
    echo "Failed to install additional packages. Please check your internet connection and try again."
    exit 1
}

# Verify installations
echo "Verifying installations..."
python3 --version
ansible --version
pip list | grep -E "omsdk|redfish|ansible-core"
ansible-galaxy collection list | grep -E "dellemc.openmanage|containers.podman|community.general"

# Create necessary directories if they don't exist
echo "Creating necessary directories..."
mkdir -p roles/harvester_install/files/{data,dnsmasq}

echo "Installation complete!"
echo "To use the installed packages, remember to activate the virtual environment with:"
echo "source harvester_venv/bin/activate"

# Deactivate the virtual environment
deactivate
