#!/usr/bin/env python3

import subprocess
import argparse
import sys

def prompt_input(prompt, default=None):
    """
    Prompt user for input with an optional default value.
    
    Args:
        prompt (str): The input prompt message
        default (str, optional): Default value if user doesn't enter anything
    
    Returns:
        str: User input or default value
    """
    if default:
        prompt_text = f"{prompt} [{default}]: "
    else:
        prompt_text = f"{prompt}: "
    
    while True:
        value = input(prompt_text).strip()
        if value:
            return value
        elif default:
            return default
        else:
            print("This field cannot be empty. Please enter a value.")

def validate_ip_address(ip):
    """
    Validate IP address format.
    
    Args:
        ip (str): IP address to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False

def validate_port(port):
    """
    Validate port number.
    
    Args:
        port (str): Port number to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except ValueError:
        return False

def get_docker_containers():
    """
    Retrieve list of running Docker container names.
    
    Returns:
        list: Names of running Docker containers
    """
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        return []

def main():
    # Create argument parser for optional command-line arguments
    parser = argparse.ArgumentParser(description='Interactive Docker Executor Removal Tool')
    parser.add_argument('--address', help='IP address of the executor to remove')
    parser.add_argument('--port', help='Port number of the executor to remove')
    parser.add_argument('--container', help='Docker container name')
    
    # Parse any provided arguments
    args = parser.parse_args()

    # Retrieve running containers
    running_containers = get_docker_containers()

    # Container Name
    if args.container and args.container in running_containers:
        container_name = args.container
    else:
        print("\nRunning Docker Containers:")
        for idx, container in enumerate(running_containers, 1):
            print(f"{idx}. {container}")
        
    # IP Address
    while True:
        address = args.address or prompt_input("Enter executor IP address to remove")
        if validate_ip_address(address):
            break
        print("Invalid IP address. Please enter a valid IP (e.g., 70.62.164.136)")

    # Port
    while True:
        port = args.port or prompt_input("Enter executor port to remove")
        if validate_port(port):
            break
        print("Invalid port number. Please enter a number between 1 and 65535")

    # Construct the docker exec command
    docker_command = [
        'docker', 'exec', '-it', 
        "6499dcc20dfb", 
        'python', '/root/app/src/cli.py', 
        'remove-executor', 
        '--address', address, 
        '--port', port
    ]

    # Confirm execution
    print("\nCommand to be executed:")
    print(' '.join(docker_command))
    
    confirm = input("\nAre you sure you want to remove this executor? (yes/no): ").lower()
    if confirm in ['yes', 'y']:
        try:
            # Execute the command
            result = subprocess.run(docker_command, check=True)
            print("\nExecutor removal command executed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"\nError executing command: {e}")
            sys.exit(1)
    else:
        print("Operation cancelled.")

if __name__ == '__main__':
    main()
