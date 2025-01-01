#!/usr/bin/env python3

import subprocess
import time
from typing import List, Dict

def delete_executor(ip: str) -> bool:
    sql_command = f"DELETE FROM executor WHERE address = '{ip}';"
    psql_command = f"psql -U postgres -d compute-subnet-db -c \"{sql_command}\""
    
    docker_command = [
        'docker', 
        'exec', 
        '-i',
        'miner-db-1',
        '/bin/sh', 
        '-c',
        psql_command
    ]
    
    try:
        subprocess.run(docker_command, check=True, capture_output=True)
        print(f"Deleted executor: {ip}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error deleting executor {ip}: {e}")
        return False

def add_executor(ip: str, port: str, validator: str) -> bool:
    docker_command = [
        'docker', 
        'exec', 
        '-i',
        '18fca0e8820d',  # Fixed container ID
        'python', 
        '/root/app/src/cli.py',
        'add-executor',
        '--validator', validator,
        '--port', port,
        '--address', ip
    ]
    
    print(' '.join(docker_command))
    
    try:
        subprocess.run(docker_command, check=True)
        print(f"Added executor: {ip}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error adding executor {ip}: {e}")
        return False

def get_executor_details() -> List[Dict[str, str]]:
    executors = []
    while True:
        print("\n=== Add Executor Details ===")
        ip = input("Enter IP address (or 'done' to finish): ").strip()
        
        if ip.lower() == 'done':
            if not executors:
                print("Please add at least one executor!")
                continue
            break
            
        port = input("Enter port: ").strip()
        validator = input("Enter validator key: ").strip()
        
        executors.append({
            'ip': ip,
            'port': port,
            'validator': validator
        })
        
        print(f"\nAdded executor: {ip}:{port} with validator {validator}")
        print("\nCurrent executors:")
        for idx, exec in enumerate(executors, 1):
            print(f"{idx}. {exec['ip']}:{exec['port']} - {exec['validator']}")
        
        add_more = input("\nAdd another executor? (y/n): ").strip().lower()
        if add_more != 'y':
            break
    
    return executors

def refresh_executors() -> None:
    executors = get_executor_details()
    
    for executor in executors:
        delete_executor(executor['ip'])
        time.sleep(2)  # Small delay between delete and add
        add_executor(executor['ip'], executor['port'], executor['validator'])

def main():
    print("\n=== Executor Auto-Refresh Tool ===")
    
    # Get all executor details
    executors = get_executor_details()

    # Get refresh interval
    while True:
        try:
            interval = int(input("\nEnter refresh interval in seconds (minimum 30): "))
            if interval < 30:
                print("Interval must be at least 30 seconds!")
                continue
            break
        except ValueError:
            print("Please enter a valid number!")
    
    print(f"\nWill refresh {len(executors)} executors every {interval} seconds")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            refresh_executors()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nScript terminated by user")

if __name__ == '__main__':
    main()