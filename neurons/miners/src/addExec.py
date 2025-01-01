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

def main():
    # Create argument parser for optional command-line arguments
    parser = argparse.ArgumentParser(description='Interactive Docker Executor Addition Tool')
    parser.add_argument('--address', help='IP address of the executor')
    parser.add_argument('--port', help='Port number of the executor')
    parser.add_argument('--validator', help='Validator key')
    
    # Parse any provided arguments
    args = parser.parse_args()

    # Interactively gather parameters
    print("Docker Executor Addition Tool")
    print("------------------------------")

    # # IP Address
    # while True:
    #     address = args.address or prompt_input("Enter IP address")
    #     if validate_ip_address(address):
    #         break
    #     print("Invalid IP address. Please enter a valid IP (e.g., 70.62.164.136)")

    # # Port
    # while True:
    #     port = args.port or prompt_input("Enter port number")
    #     if validate_port(port):
    #         break
    #     print("Invalid port number. Please enter a number between 1 and 65535")

    # # Validator Key
    # validator = args.validator or prompt_input("Enter validator key")

    # Construct the docker exec command
   

    # Confirm execution
    valis = [
         "5E1nK3myeWNWrmffVaH76f2mCFCbe9VcHGwgkfdcD7k3E8D1", #this works with proxy
         "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1", #this works with proxy
        #  "5CsvRJXuR955WojnGMdok1hbhffZyB4N5ocrv82f3p5A2zVp", #this works with 3rd proxy
        #  "5HEo565WAy4Dbq3Sv271SAi7syBSofyfhhwRNjFNSM2gP9M2", #this works with  proxy
        #  "5F2CsUDVbRbVMXTh9fAzF9GacjVX7UapvRxidrxe7z8BYckQ", #this works with proxy
        #  "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v", #this doesnt work 
        #  "5FxcZraZACr4L78jWkcYe3FHdiwiAUzrKLVtsSwkvFobBKqq", #this works with 3rd proxy
        
        #  "5HYk8DMKWK8TJyPzZJ9vmZk7B5NPCgjnZoyZ1ZsB54RXdN47", #this works with 3rd proxy
        #  "5HYk8DMKWK8TJyPzZJ9vmZk7B5NPCgjnZoyZ1ZsB54RXdN47", #this works with 3rd proxy
         
         ]

    ips = [ #8001 ports here
        {"ip":"185.141.218.60","port":"8001"},# L4 Direct call
        # {"ip":"80.188.223.202","port":"10912"},# L4 Direct call
        # {"ip":"34.222.38.86","port":"8001"},# L4 Direct call
        # {"ip":"38.29.145.12","port":"10963"},# L4 Direct call
        # {"ip":"213.180.0.35","port":"47943"},# L4 Direct call
        # {"ip":"3.38.217.223","port":"8001"},# L4 Direct call
        # {"ip":"185.141.218.198","port":"8001"}, # L4 proxy call
        # {"ip":"64.247.196.27","port":"8001"}, # 4x A6000
           ] 

    dockerHash = "d8ae7d1fffa6"

    # Keep track of assigned IPs and validators
    assigned_ips = set()
    assigned_valis = set()

    # Loop through IPs
    for ip_data in ips:
        # Skip if this IP has already been assigned
        if ip_data["ip"] in assigned_ips:
            continue
            
        # Find first unassigned validator
        for vali in valis:
            # if vali not in assigned_valis:
            docker_command = [
                'docker', 'exec', '-it',
                dockerHash,
                'python', '/root/app/src/cli.py',
                'add-executor',
                '--validator', vali,
                '--port', ip_data["port"],
                '--address', ip_data["ip"]
            ]
            
            print(' '.join(docker_command))  # Print command before executing
            
            try:
                result = subprocess.run(docker_command, check=True)
                print(f"\nAssigned IP {ip_data['ip']} to validator {vali}")
                # Mark both IP and validator as assigned
                assigned_ips.add(ip_data["ip"])
                assigned_valis.add(vali)
                # break
            except subprocess.CalledProcessError as e:
                print(f"\nError assigning IP {ip_data['ip']} to validator {vali}: {e}")
                continue

if __name__ == '__main__':
    main()
