import sys
import os
import subprocess
from datetime import datetime


# Constants
REDIRECT_PORT = 8989
CONTAINER_NAME = "udpr"


def validate_date(date_str):
    """Validate date format (YYYY-MM-DD)."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def setup_iptables(net_interface, ports):
    """Set up iptables rules."""
    ports = sorted(ports)
    start = 1
    for n in ports:
        if n == 1:
            start += 1
            continue

        cmd = [
            "iptables", "-t", "nat", "-I", "PREROUTING", "-i", net_interface,
            "-p", "udp", "--dport", f"{start}:{n-1}", "-j", "REDIRECT", "--to-ports", str(REDIRECT_PORT)
        ]
        subprocess.run(cmd, check=True)
        start = n + 1

    if ports[-1] != 65535:
        cmd = [
            "iptables", "-t", "nat", "-I", "PREROUTING", "-i", net_interface,
            "-p", "udp", "--dport", f"{start}:65535", "-j", "REDIRECT", "--to-ports", str(REDIRECT_PORT)
        ]
        subprocess.run(cmd, check=True)

    print("IPTABLES SUCCESS")


def add_user(username, password, expire_date):
    """Add a user to the container."""
    if not validate_date(expire_date):
        print("Error: Invalid date format. Use YYYY-MM-DD.")
        sys.exit(1)

    subprocess.run(["docker", "exec", "-it", CONTAINER_NAME, "adduser", username, "--disabled-password"], check=True)
    subprocess.run(["docker", "exec", "-it", CONTAINER_NAME, "chage", "-E", expire_date, username], check=True)
    cmd_change_password = f"docker exec -it {CONTAINER_NAME} sh /root/useradd.sh \"{username}\" \"{password}\""
    subprocess.run(cmd_change_password, shell=True, check=True)

    print(f"User '{username}' added successfully.")


def delete_user(username):
    """Delete a user from the container."""
    subprocess.run(["docker", "exec", "-it", CONTAINER_NAME, "userdel", username], check=True)
    print(f"User '{username}' deleted successfully.")


def main():
    if len(sys.argv) < 2:
        print("Error: Action is required (e.g., 'route' or 'manage').")
        sys.exit(1)

    action = sys.argv[1]

    if action == "route":
        if len(sys.argv) < 4:
            print("Error: Network interface and excluded ports are required (e.g., 'eth0 53,989').")
            sys.exit(1)

        net_interface = sys.argv[2]
        ports_arg = sys.argv[3]
        try:
            ports = [int(num) for num in ports_arg.split(",")]
        except ValueError:
            print("Error: Ports must be integers separated by commas.")
            sys.exit(1)

        setup_iptables(net_interface, ports)

    elif action == "manage":
        if len(sys.argv) < 3:
            print("Error: Sub-action ('add' or 'del') is required.")
            sys.exit(1)

        sub_action = sys.argv[2]

        if sub_action == "add":
            if len(sys.argv) < 6:
                print("Error: Username, password, and expiry date are required (e.g., 'add user pass 2025-05-01').")
                sys.exit(1)

            username = sys.argv[3]
            password = sys.argv[4]
            expire_date = sys.argv[5]
            add_user(username, password, expire_date)

        elif sub_action == "del":
    if len(sys.argv) < 4:
        print("Error: Username is required to delete.")
        sys.exit(1)

    username = sys.argv[3]
    try:
        # Run the user deletion command in the container
        subprocess.run(["docker", "exec", "-it", CONTAINER_NAME, "userdel", username], check=True)
        print(f"User '{username}' deleted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to delete user '{username}'. Details: {e}")
        sys.exit(1)

            username = sys.argv[3]
            delete_user(username)

        else:
            print("Error: Invalid sub-action. Use 'add' or 'del'.")
            sys.exit(1)

    else:
        print("Error: Invalid action. Use 'route' or 'manage'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
