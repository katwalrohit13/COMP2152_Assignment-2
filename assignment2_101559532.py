"""
Author: Rohit Kumar
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""

import socket
import threading
import sqlite3
import os
import platform
import datetime

print("Python Version:", platform.python_version())
print("Operating System:", os.name)

# This dictionary holds common port numbers and their service names

common_ports = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt"
}


class NetworkTool:
    def __init__(self, target):
        self.__target = target

    # Q3: What is the benefit of using @property and @target.setter?
    # Using @property helps us access private variables safely.
    # The setter allows us to check values before updating them.
   
 # This prevents invalid inputs like empty strings and keeps the object consistent.

    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, value):
        if value == "":
            print("Error: Target cannot be empty")
        else:
            self.__target = value

    def __del__(self):
        print("NetworkTool instance destroyed")


# Q1: How does PortScanner reuse code from NetworkTool?
# PortScanner inherits from NetworkTool, so it automatically gets features like the constructor.
# It uses super().__init__(target) instead of rewriting the same logic again.
# This reduces duplication and keeps the code simple and maintainable.

class PortScanner(NetworkTool):
    def __init__(self, target):
        super().__init__(target)
        self.scan_results = []
        self.lock = threading.Lock()

    def __del__(self):
        print("PortScanner instance destroyed")
        super().__del__()

    def scan_port(self, port):

        # Q4: What would happen without try-except here?
        # Without try-except, any socket error could stop the program.
        # If a port cannot be reached, it may raise an exception.
        # This would interrupt the scanning process instead of continuing.

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)

            result = sock.connect_ex((self.target, port))
            status = "Open" if result == 0 else "Closed"
            service = common_ports.get(port, "Unknown")

            with self.lock:
                self.scan_results.append((port, status, service))

        except socket.error as err:
            print(f"Error scanning port {port}: {err}")

        finally:
            sock.close()

    def get_open_ports(self):
        open_ports = [item for item in self.scan_results if item[1] == "Open"]
        return open_ports

    # Q2: Why do we use threading instead of scanning one port at a time?
    # Threading allows multiple ports to be scanned simultaneously.
    # If we scan sequentially, checking many ports would take a long time.
    # Using threads improves performance and reduces total scanning time.

    def scan_range(self, start_port, end_port):
        thread_list = []

        for port in range(start_port, end_port + 1):
            t = threading.Thread(target=self.scan_port, args=(port,))
            thread_list.append(t)

        for t in thread_list:
            t.start()

        for t in thread_list:
            t.join()


def save_results(target, results):
    try:
        conn = sqlite3.connect("scan_history.db")
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT,
            port INTEGER,
            status TEXT,
            service TEXT,
            scan_date TEXT
        )
        """)

        for port, status, service in results:
            cur.execute(
                "INSERT INTO scans (target, port, status, service, scan_date) VALUES (?, ?, ?, ?, ?)",
                (target, port, status, service, str(datetime.datetime.now()))
            )

        conn.commit()
        conn.close()

    except sqlite3.Error as e:
        print("Database error:", e)


def load_past_scans():
    try:
        conn = sqlite3.connect("scan_history.db")
        cur = conn.cursor()

        cur.execute("SELECT * FROM scans")
        rows = cur.fetchall()

        for row in rows:
            print(f"[{row[5]}] {row[1]} : Port {row[2]} ({row[4]}) - {row[3]}")

        conn.close()

    except:
        print("No past scans found.")


if __name__ == "__main__":
    try:
        target = input("Enter target IP (default 127.0.0.1): ")
        if target.strip() == "":
            target = "127.0.0.1"

        start_port = int(input("Enter start port (1-1024): "))
        end_port = int(input("Enter end port (1-1024): "))

        if start_port < 1 or end_port > 1024:
            print("Port must be between 1 and 1024.")
            exit()

        if end_port < start_port:
            print("End port must be greater than or equal to start port.")
            exit()

    except ValueError:
        print("Invalid input. Please enter a valid integer.")
        exit()

    scanner = PortScanner(target)

    print(f"Scanning {target} from port {start_port} to {end_port}...")
    scanner.scan_range(start_port, end_port)

    open_ports = scanner.get_open_ports()

    print(f"\nScan summary for {target}")
    for port, status, service in open_ports:
        print(f"Port {port}: {status} ({service})")

    print("------")
    print(f"Total open ports found: {len(open_ports)}")
    

    save_results(target, scanner.scan_results)

    choice = input("Would you like to see past scan history? (yes/no): ")
    if choice.lower() == "yes":
        load_past_scans()


# Q5: New Feature Proposal
# I would add an option to show only closed ports instead of open ones.
# This can be implemented using a list comprehension that filters results where status is "Closed".
# It would help users quickly identify unused ports.
# Diagram: See diagram_101559532.png in the repository root