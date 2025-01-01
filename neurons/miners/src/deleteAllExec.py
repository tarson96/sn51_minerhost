#!/usr/bin/env python3

import subprocess
import sys

def delete_single_executor(ip_address):
    """Delete a single executor from database by IP address"""
    
    # SQL command to delete specific executor
    sql_command = f"DELETE FROM executor WHERE address = '{ip_address}';"
    
    # Full postgres command
    psql_command = f"psql -U postgres -d compute-subnet-db -c \"{sql_command}\""
    
    # Full docker command
    docker_command = [
        'docker', 
        'exec', 
        '-it',
        'miner-db-1',  # container name
        '/bin/sh', 
        '-c',
        psql_command
    ]
    
    try:
        # Execute command
        result = subprocess.run(
            docker_command,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Check if deletion was successful
        if "DELETE" in result.stdout:
            count = result.stdout.strip().split('\n')[0].split()[1]
            if count == "0":
                print(f"\nNo executor found with IP address: {ip_address}")
            else:
                print(f"\nSuccessfully deleted executor with IP: {ip_address}")
        
        # Show current state
        show_current_state()
            
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

def delete_single_executor_uid(uid):
    """Delete a single executor from database by IP address"""
    
    # SQL command to delete specific executor
    sql_command = f"DELETE FROM executor WHERE uuid = '{uid}';"
    
    # Full postgres command
    psql_command = f"psql -U postgres -d compute-subnet-db -c \"{sql_command}\""
    
    # Full docker command
    docker_command = [
        'docker', 
        'exec', 
        '-it',
        'miner-db-1',  # container name
        '/bin/sh', 
        '-c',
        psql_command
    ]
    
    try:
        # Execute command
        result = subprocess.run(
            docker_command,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Check if deletion was successful
        if "DELETE" in result.stdout:
            count = result.stdout.strip().split('\n')[0].split()[1]
            if count == "0":
                print(f"\nNo executor found with uid: {uid}")
            else:
                print(f"\nSuccessfully deleted executor with uid: {uid}")
        
        # Show current state
        show_current_state()
            
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)
        

def delete_all_executors():
    """Delete all executors from database using docker exec command"""
    
    # SQL command to delete all executors
    sql_command = "DELETE FROM executor;"
    
    # Full postgres command
    psql_command = f"psql -U postgres -d compute-subnet-db -c \"{sql_command}\""
    
    # Full docker command
    docker_command = [
        'docker', 
        'exec', 
        '-it',
        'miner-db-1',  # container name
        '/bin/sh', 
        '-c',
        psql_command
    ]
    
    try:
        # Execute command
        result = subprocess.run(
            docker_command,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Check if deletion was successful
        if "DELETE" in result.stdout:
            count = result.stdout.strip().split('\n')[0].split()[1]
            print(f"\nSuccessfully deleted {count} executor(s)")
        else:
            print("\nNo executors found in the database")
            
        # Show current state
        show_current_state()
            
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

def show_current_state():
    """Show current executors in database"""
    select_command = "SELECT * FROM executor;"
    psql_command = f"psql -U postgres -d compute-subnet-db -c \"{select_command}\""
    
    docker_command = [
        'docker', 
        'exec', 
        '-it',
        'miner-db-1',
        '/bin/sh', 
        '-c',
        psql_command
    ]
    
    try:
        result = subprocess.run(
            docker_command,
            capture_output=True,
            text=True,
            check=True
        )
        print("\nCurrent executors in database:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error checking database state: {e}")

def main():
    print("\n=== Executor Deletion Tool ===\n")
    
    # Show current state before deletion
    print("Current executors in database:")
    show_current_state()
    
    # Ask user for deletion mode
    print("\nDelete options:")
    print("1. Delete single executor by IP")
    print("2. Delete ALL executors")
    print("3. Delete by uid")
    choice = input("Enter your choice: ")
    
    if choice == "1":
        ip_address = input("Enter the IP address to delete: ")
        delete_single_executor(ip_address)
    
    elif choice == "2":
        # Confirm deletion
        print("\nWARNING: This will delete ALL executors from the database!")
        confirm = input("Are you sure you want to proceed? (yes/no): ")
        
        if confirm.lower() in ['yes', 'y']:
            delete_all_executors()
        else:
            print("Operation cancelled")
    elif choice == "3":
        # Confirm deletion
        uid = input("Enter uid: ")
        confirm = input("Are you sure you want to proceed? (yes/no): ")
        if confirm.lower() in ['yes', 'y']:
            delete_single_executor_uid(uid)

        else:
            print("Operation cancelled")
    else:
        print("Invalid choice. Please run the script again.")

if __name__ == "__main__":
    main()