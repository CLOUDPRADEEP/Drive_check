Here is the content for your `README.md` file:

---

# Synology Drive Status Checker

## Overview

This script automates the process of checking the availability of specific directories (`/usr/local` and `/usr/local/backup`) on a list of remote servers. It also validates the presence of Synology drive entries in the `/etc/fstab` file on those servers. The results are saved in a CSV file and logged for auditing purposes.

## Features

- **Disk Space Check**: Executes the `df -kh` command to verify the availability of `/usr/local` and `/usr/local/backup` directories.
- **Synology Drive Validation**: Identifies entries in the `/etc/fstab` file that start with an IP address to confirm Synology drive configuration.
- **Detailed Output**: Outputs the results in a CSV file with columns for server, sitename, disk status, Synology drive status, and a summary.
- **Multiple Passwords Support**: Tries up to three passwords for SSH login to handle servers with different credentials.
- **Timeout Handling**: Ensures that the disk status command does not hang indefinitely by enforcing a timeout of 60 seconds.
- **Logging**: Logs all operations and errors in `process.log`.

## Output File Format

The script generates a CSV file with the following columns:

| Server         | Sitename        | usr/local      | synology_drive | Disk Status                         | Fstab Record                   | Summary                                              |
|----------------|-----------------|----------------|----------------|--------------------------------------|---------------------------------|------------------------------------------------------|
| `Server`       | `Sitename`      | `Available`/`Unavailable` | `Available`/`Unavailable` | Disk command output or timeout/error | Last relevant entry from `/etc/fstab` or error | Summary of the findings (e.g., drive availability) |

## How It Works

1. Reads the list of servers and site names from `ip.txt` (format: `IP:Sitename`).
2. Attempts to log in to each server using SSH with multiple passwords.
3. Executes the `df -kh` command to check the availability of `/usr/local` and `/usr/local/backup`.
4. Reads the last three lines of `/etc/fstab` to look for Synology drive entries starting with an IP address.
5. Determines the status of the Synology drive based on the disk command and `fstab` validation.
6. Logs all actions and errors in `process.log`.
7. Saves the results in `output.csv`.

## Prerequisites

- Python 3.x
- Required Python libraries:
  - `paramiko`
  - `pandas`
  - `re`

## Installation

1. Clone this repository or copy the script file to your local system.
2. Install required libraries:
   ```bash
   pip install paramiko pandas
   ```

## Usage

1. Prepare an `ip.txt` file with the format:
   ```
   IP_ADDRESS:SITENAME
   ```
   Example:
   ```
   192.168.1.1:Server1
   192.168.1.2:Server2
   ```

2. Run the script:
   ```bash
   python check_disk_fstab.py
   ```

3. The results will be saved in `output.csv`, and logs will be available in `process.log`.

## Example Output

### CSV File (`output.csv`)

| Server         | Sitename        | usr/local      | synology_drive | Disk Status                         | Fstab Record                   | Summary                                              |
|----------------|-----------------|----------------|----------------|--------------------------------------|---------------------------------|------------------------------------------------------|
| 192.168.1.1    | Server1         | Available      | Available      | `/usr/local`, `/usr/local/backup`   | `192.168.1.100:/vol1/backup`   | Synology drive is available and matches fstab entry. |
| 192.168.1.2    | Server2         | Unavailable    | Unavailable    | Disk check failed or timed out.     | No relevant entries in fstab.  | Synology drive missing and no entry in fstab.        |

---
