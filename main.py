import paramiko
import subprocess
import threading
import time
import pandas as pd
import re

# File containing IP addresses
ip_file = "ip.txt"

# Output CSV file
output_file = "output.csv"

# Log file name
log_file = "process.log"

# Username for SSH(remoteservers)
username = "pradeep.sahoo"

# Timeout for disk space check (in seconds)
disk_check_timeout = 60

# Passwords for SSH
passwords = ["password1", "Password2", "Password3"]

def log_message(message):
    """Write a message to the log file."""
    with open(log_file, "a") as log:
        log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def ssh_connect_with_passwords(server):
    """Attempt to connect to the server using multiple passwords."""
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for password in passwords:
        try:
            ssh_client.connect(server, username=username, password=password, timeout=30)
            log_message(f"Successfully connected to {server} with one of the passwords.")
            return ssh_client
        except paramiko.AuthenticationException:
            log_message(f"Authentication failed for {server} with a password.")
        except Exception as e:
            log_message(f"Error connecting to {server}: {str(e)}")
    raise Exception(f"All password attempts failed for {server}.")

def check_disk_status(server, ssh_client):
    """Check disk status and extract relevant information."""
    try:
        stdin, stdout, stderr = ssh_client.exec_command("df -kh | grep -E '/usr/local$|/usr/local/backup$'")
        # Wait for command to complete or timeout
        start_time = time.time()
        while not stdout.channel.exit_status_ready():
            if time.time() - start_time > disk_check_timeout:
                stdout.channel.close()
                stderr.channel.close()
                raise TimeoutError("Disk check timed out.")
        output = stdout.read().decode()
        if not output:
            log_message(f"No output from disk status command on {server}.")
            return None
        # Parse disk status for /usr/local and /usr/local/backup
        usr_local_status = "Available" if "/usr/local" in output else "Unavailable"
        usr_local_backup_status = "Available" if "/usr/local/backup" in output else "Unavailable"
        return usr_local_status, usr_local_backup_status, output
    except TimeoutError as te:
        log_message(f"Disk check timed out on {server}. Checking fstab.")
        return "Unavailable", "Unavailable", None
    except Exception as e:
        return f"Error: {str(e)}", "Unavailable", None

def read_fstab(server, ssh_client):
    """Read the last 3 lines of the /etc/fstab file and check for Synology drive entries."""
    try:
        stdin, stdout, stderr = ssh_client.exec_command("tail -n 3 /etc/fstab")
        output = stdout.read().decode()
        if not output.strip():
            log_message(f"No relevant entries found in fstab on {server}.")
            return None
        # Check for lines starting with an IP address
        synology_entry = None
        for line in output.splitlines():
            if re.match(r"^\d+\.\d+\.\d+\.\d+", line):
                synology_entry = line
                break
        if synology_entry:
            log_message(f"Synology drive entry found in fstab on {server}: {synology_entry}")
            return synology_entry
        else:
            log_message(f"No Synology drive entry found in fstab on {server}.")
            return None
    except Exception as e:
        return f"Error: {str(e)}"

def process_server(server, sitename):
    """Process each server to check disk status and fstab."""
    result = {
        "Server": server,
        "Sitename": sitename,
        "usr/local": "",
        "synology_drive": "",
        "Disk Status": "",
        "Fstab Record": "",
        "Summary": ""
    }
    try:
        # Connect to the server using available passwords
        ssh_client = ssh_connect_with_passwords(server)

        log_message(f"Connected to {server} ({sitename}).")

        # Check disk status
        usr_local_status, usr_local_backup_status, disk_status_output = check_disk_status(server, ssh_client)
        fstab_status = read_fstab(server, ssh_client)

        # Determine Synology drive status
        if usr_local_backup_status == "Available":
            if fstab_status and re.match(r"^\d+\.\d+\.\d+\.\d+", fstab_status):
                synology_status = "Available"
                summary = "Synology drive is available and matches fstab entry."
            else:
                synology_status = "Unavailable"
                summary = "Synology drive present but no matching fstab entry."
        else:
            synology_status = "Unavailable"
            if fstab_status:
                summary = "Synology drive missing but entry found in fstab."
            else:
                summary = "Synology drive missing and no entry in fstab."

        # Update result
        result["usr/local"] = usr_local_status
        result["synology_drive"] = synology_status
        result["Disk Status"] = disk_status_output if disk_status_output else "Disk check failed or timed out."
        result["Fstab Record"] = fstab_status if fstab_status else "No relevant entries in fstab."
        result["Summary"] = summary

        ssh_client.close()
    except Exception as e:
        result["usr/local"] = "Error"
        result["synology_drive"] = "Error"
        result["Disk Status"] = f"Error: {str(e)}"
        result["Fstab Record"] = "N/A"
        result["Summary"] = "Error during processing."
        log_message(f"Error processing {server} ({sitename}): {str(e)}")
    return result

# Read IP addresses and site names from file
with open(ip_file, "r") as file:
    servers = [line.strip().split(":") for line in file if line.strip()]

# Collect results
results = []
for server, sitename in servers:
    log_message(f"Starting processing for {server} ({sitename}).")
    print(f"Processing server: {server} ({sitename})")
    result = process_server(server, sitename)
    results.append(result)
    log_message(f"Completed processing for {server} ({sitename}).")

# Save results to a CSV file
df = pd.DataFrame(results)
df.to_csv(output_file, index=False)

log_message(f"Output has been saved to {output_file}.")
print(f"Output has been saved to {output_file}.")
