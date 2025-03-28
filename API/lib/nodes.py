import json
import subprocess
import ipaddress
import ftplib
import socket
import re
import threading
from concurrent.futures import ThreadPoolExecutor
import openai
from datetime import datetime


class BaseNode:
    def __init__(self, node_id, name, parameters, previous_input=None):
        self.node_id = node_id
        self.name = name
        self.parameters = parameters
        self.connections = []
        self.previous_input = previous_input
        self.output = None
        self.node_type = self.__class__.__name__

    def add_connection(self, target_node_id):
        self.connections.append(target_node_id)

    def execute(self, inputs):
        self.output = {
            "output": f"{self.name} processed {inputs}",
            "success": {},
            "data": {"info": inputs}
        }
        return self.output

class PingNode(BaseNode):
    def __init__(self, node_id, name, parameters):
        super().__init__(node_id, name, parameters)

    def execute(self, input_data=None):
        ip = self.parameters.get("ip", "127.0.0.1")
        option = self.parameters.get("option", "-c 3")
        cmd = f"ping {option} {ip}"
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                executable="/bin/bash"
            )
            self.output = {
                "output": "Good",
                "success": {ip: True},
                "data": {
                    ip: {
                        "status": "Good",
                        "details": result.stdout.strip()
                    }
                }
            }
        except subprocess.CalledProcessError as e:
            self.output = {
                "output": "Error",
                "success": {},
                "data": {
                    ip: {
                        "status": "Error",
                        "details": e.stderr.strip()
                    }
                }
            }
        return self.output

class FTPAnonymousNode(BaseNode):
    def __init__(self, node_id, name, parameters):
        super().__init__(node_id, name, parameters)

    def execute(self, input_data=None):
        ip_range = self.parameters.get("ip", "127.0.0.1/32")
        max_threads = self.parameters.get("threads", 20)
        timeout = self.parameters.get("timeout", 5)
        ftp_port = self.parameters.get("port", 21)

        success = {}
        data = {}
        ip_list = [str(ip) for ip in ipaddress.ip_network(ip_range, strict=False)]

        def check_ftp(ip):
            try:
                ftp = ftplib.FTP()
                ftp.connect(ip, ftp_port, timeout=timeout)
                ftp.login("anonymous", "anonymous@domain.com")
                ftp.quit()
                success[ip] = True
                data[ip] = {"status": "Good", "details": "Anonymous login successful"}
            except ftplib.error_perm as e:
                data[ip] = {"status": "Error", "details": str(e)}
            except Exception as e:
                data[ip] = {"status": "Error", "details": str(e)}

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            executor.map(check_ftp, ip_list)

        self.output = {
            "output": "Good" if success else "Error",
            "success": success,
            "data": data
        }
        return self.output

class SMBClientNode(BaseNode):
    def __init__(self, node_id, name, parameters):
        super().__init__(node_id, name, parameters)

    def execute(self, input_data=None):
        ip_range = self.parameters.get("ip", "127.0.0.1/32")
        max_threads = self.parameters.get("threads", 20)
        timeout = self.parameters.get("timeout", 5)

        success = {}
        data = {}
        ip_list = [str(ip) for ip in ipaddress.ip_network(ip_range, strict=False)]

        def check_host(ip):
            try:
                result = subprocess.run(
                    ["smbclient", "-L", f"//{ip}/", "-N"],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                if "Sharename" in result.stdout and "Disk" in result.stdout:
                    success[ip] = True
                    data[ip] = {"status": "Good", "details": "Guest login success"}
                else:
                    data[ip] = {"status": "Error", "details": result.stderr.strip() or "Access denied"}
            except subprocess.TimeoutExpired:
                data[ip] = {"status": "Timeout", "details": "Connection timed out"}
            except Exception as e:
                data[ip] = {"status": "Error", "details": str(e)}

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            executor.map(check_host, ip_list)

        self.output = {
            "output": "Good" if success else "Error",
            "success": success,
            "data": data
        }
        return self.output

class NmapNode(BaseNode):
    def __init__(self, node_id, name, parameters):
        super().__init__(node_id, name, parameters)

    def execute(self, input_data=None):
        ip = self.parameters.get("ip", "127.0.0.1")
        port_range = self.parameters.get("port", "1-1024")
        option = self.parameters.get("option", "-sS")
        cmd = f"nmap {option} -p {port_range} {ip}"

        success = {}
        data = {}

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                executable="/bin/bash"
            )

            output = result.stdout
            current_ip = None

            for line in output.splitlines():
                ip_match = re.search(r"Nmap scan report for ([\d\.]+)", line)
                port_match = re.match(r"^(\d+)/tcp\s+(open|closed|filtered)", line)

                if ip_match:
                    current_ip = ip_match.group(1)
                    data[current_ip] = {"open": [], "closed": []}

                elif port_match and current_ip:
                    port = int(port_match.group(1))
                    state = port_match.group(2)
                    if state == "open":
                        data[current_ip]["open"].append(port)
                    else:
                        data[current_ip]["closed"].append(port)

            for ip_addr, ports in data.items():
                if ports["open"]:
                    success[ip_addr] = ports["open"]

            self.output = {
                "output": "Good" if success else "Error",
                "success": success,
                "data": data
            }

        except subprocess.CalledProcessError as e:
            self.output = {
                "output": "Error",
                "success": {},
                "data": {
                    ip: {
                        "open": [],
                        "closed": [],
                        "error": e.stderr.strip() if e.stderr else str(e)
                    }
                }
            }

        return self.output


class BannerGrabNode(BaseNode):
    def __init__(self, node_id, name, parameters):
        super().__init__(node_id, name, parameters)

    def execute(self, input_data=None):
        ip_range = self.parameters.get("ip", "127.0.0.1/32")
        port = int(self.parameters.get("port", 80))
        max_threads = int(self.parameters.get("threads", 20))
        timeout = float(self.parameters.get("timeout", 3.0))

        data = {}
        success = {}
        ip_list = [str(ip) for ip in ipaddress.ip_network(ip_range, strict=False)]

        def grab_banner(ip):
            try:
                with socket.create_connection((ip, port), timeout=timeout) as s:
                    s.settimeout(timeout)
                    banner = s.recv(1024).decode(errors="ignore").strip()
                    success[ip] = banner
                    data[ip] = {"status": "Good", "details": banner}
            except socket.timeout:
                data[ip] = {"status": "Timeout", "details": "Connection timed out"}
            except Exception as e:
                data[ip] = {"status": "Error", "details": str(e)}

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            executor.map(grab_banner, ip_list)

        self.output = {
            "output": "Good" if success else "Error",
            "success": success,
            "data": data
        }
        return self.output

class MergeNode(BaseNode):
    def __init__(self, node_id, name, parameters, expected_inputs):
        super().__init__(node_id, name, parameters)
        self.expected_inputs = expected_inputs
        self.lock = threading.Lock()
        self.collected_inputs = []
        self.ready_event = threading.Event()

    def execute(self, input_data):
        with self.lock:
            self.collected_inputs.append(input_data)
            if len(self.collected_inputs) >= self.expected_inputs:
                self.ready_event.set()

        self.ready_event.wait()
        self.output = {
            "output": f"[MergeNode: {self.name}] Merged inputs",
            "success": {},
            "data": {"merged_data": self.collected_inputs}
        }
        return self.output




class NMAPVulnNode(BaseNode):
    def __init__(self, node_id, name, parameters):
        super().__init__(node_id, name, parameters)
        self.node_type = "NMAPVulnNode"

    def execute(self, input_data=None):
        ip = self.parameters.get("ip", "127.0.0.1")
        port_range = self.parameters.get("port", "1-1024")
        script = self.parameters.get("script", "vulners")
        option = self.parameters.get("option", "-sV")
        cmd = f"nmap {option} --script {script} -p {port_range} {ip}"

        success = {}
        data = {}

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                executable="/bin/bash"
            )

            output = result.stdout
            current_ip = None
            current_port = None
            port_info = {}

            for line in output.splitlines():
                ip_match = re.search(r"Nmap scan report for ([\d\.]+)", line)
                port_match = re.match(r"^(\d+)/tcp\s+(open|closed|filtered)\s+(\S+)", line)
                vuln_script = re.match(r"^\|_(smb-vuln-\S+):\s+(.*)", line)
                vuln_detail = re.match(r"^\|\s+(.*)", line)

                if ip_match:
                    current_ip = ip_match.group(1)
                    data[current_ip] = {"open": [], "closed": []}
                    port_info = {}
                elif port_match:
                    current_port = int(port_match.group(1))
                    state = port_match.group(2)
                    service = port_match.group(3)
                    port_data = {
                        "port": current_port,
                        "service": service,
                        "vulnerabilities": []
                    }
                    if state == "open":
                        data[current_ip]["open"].append(port_data)
                        port_info[current_port] = port_data
                    else:
                        data[current_ip]["closed"].append(current_port)
                elif vuln_script and current_port is not None:
                    script_name = vuln_script.group(1)
                    vuln_state = vuln_script.group(2).strip()
                    port_info[current_port]["vulnerabilities"].append({
                        "script": script_name,
                        "state": vuln_state
                    })
                elif vuln_detail and current_port is not None and data[current_ip]["open"]:
                    vuln_text = vuln_detail.group(1).strip()
                    last_vuln = data[current_ip]["open"][-1]["vulnerabilities"][-1]
                    if "details" not in last_vuln:
                        last_vuln["details"] = []
                    last_vuln["details"].append(vuln_text)

            for ip_addr, ports in data.items():
                open_ports = [p["port"] for p in ports["open"] if p["vulnerabilities"]]
                if open_ports:
                    success[ip_addr] = open_ports

            self.output = {
                "output": "Good" if success else "Error",
                "success": success,
                "data": data
            }

        except subprocess.CalledProcessError as e:
            self.output = {
                "output": "Error",
                "success": {},
                "data": {
                    ip: {
                        "open": [],
                        "closed": [],
                        "error": e.stderr.strip() if e.stderr else str(e)
                    }
                }
            }

        return self.output





class Workflow:
    def __init__(self, output_file="workflow_results.json"):
        self.nodes = {}
        self.incoming_count = {}
        self.results = {}
        self.output_file = output_file

    def add_node(self, node):
        self.nodes[node.node_id] = node
        self.incoming_count[node.node_id] = 0

    def add_nodes_by_id(self, nodes_dict, node_ids):
        for nid in node_ids:
            if nid in nodes_dict:
                self.add_node(nodes_dict[nid])
            else:
                print(f"[!] Warning: Node ID '{nid}' not found in provided node dictionary.")

    def connect_nodes(self, from_node_id, to_node_id):
        if from_node_id in self.nodes and to_node_id in self.nodes:
            self.nodes[from_node_id].add_connection(to_node_id)
            self.incoming_count[to_node_id] += 1

    def execute(self):
        executed = set()
        lock = threading.Lock()

        def execute_node(node_id, input_data=None):
            node = self.nodes[node_id]
            print(f"[+] Starting execution: {node.name} ({node.node_type})")

            output = node.execute(input_data)

            with lock:
                self.results[node_id] = output
                executed.add(node_id)
                print(f"[✓] Finished execution: {node.name} -> {output['output']}")
                self._save_results()

            threads = []
            for next_node_id in node.connections:
                print(f"[→] Passing output from {node.name} to {self.nodes[next_node_id].name}")
                t = threading.Thread(target=execute_node, args=(next_node_id, output["data"]))
                t.start()
                threads.append(t)

            for t in threads:
                t.join()

        # Start with root nodes (no incoming connections)
        root_nodes = [nid for nid in self.nodes if self.incoming_count[nid] == 0]

        threads = []
        for root_id in root_nodes:
            t = threading.Thread(target=execute_node, args=(root_id, {"input": "Start Input"}))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        return self.results

    def _save_results(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(self.output_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"[💾] Workflow results saved to {self.output_file}")