# At the top
from lib.nodes import PingNode, NmapNode, SMBClientNode, FTPAnonymousNode, BannerGrabNode, Workflow, NMAPVulnNode, SMBMountNode
from lib.ai import ChatGPTNode
from lib.exploit import BlueNode
import lib.prompt
import os

def build_nodes():
    DEFAULT_IP = "127.0.0.1"
    IP_FILE = "./target_ip.txt"

    if not os.path.exists(IP_FILE):
        with open(IP_FILE, "w") as f:
            f.write(DEFAULT_IP)

    with open(IP_FILE, "r") as f:
        ip = f.read().strip()
    
    ping1_parameters = {
        "ip": ip,
        "option": "-c 4"
    }

    ping1 = PingNode("1","ping1",parameters=ping1_parameters)


    initial_nmap_parameters = {
        "ip": ip,
        "port": "21,22,23,25,80,88,135,443,445,3389",
        "option": "-sV --script smb-enum-shares --open"
    }
    initial_nmap_node = NmapNode('2','initial_nmap',initial_nmap_parameters)



    smb_nmap_parameters = {
        "ip": ip,
        "port": "445",
        "option": "-sV --script smb-vuln* --open"
    }
    smb_nmap_node = NmapNode('3', 'smb_nmap', smb_nmap_parameters)


    smbclient_parameters = {
        "ip": ip,
        "threads": 30 
    }

    smbclient_node = SMBClientNode(
        '4',
        'smbclient', 
        smbclient_parameters
    )

    ftp_parameters = {
        "ip": ip,
            "threads": 30,
            "timeout": 4,
            "port": 21
    }

    ftp_anonymous_node = FTPAnonymousNode(
        node_id="5",
        name="FTP Anonymous Scanner",
        parameters=ftp_parameters
    )


    banner_node = BannerGrabNode(
        node_id="6",
        name="Generic Banner Grabber",
        parameters={
            "ip": ip,
            "port": 21,  # Try FTP, SSH, etc.
            "threads": 50,
            "timeout": 2.5
        }
    )


    chat_node = ChatGPTNode(
        node_id="7",
        name="Summarizer",
        parameters={
            "api_key": "OPENAI_API",
            "model": "gpt-3.5-turbo",
            "prompt": "Summarize the following data: Hello World!!"
        }
    )


    blue_node = BlueNode(
        node_id="8",
        name="CheckMS17",
        parameters={
            "ip": ip,           # IP to test
        }
    )


    nmap_vuln_parameters = {
        "ip": "10.10.10.40",
        "port": "445",
        "script": "vuln",
        "option": "-sV"
    }

    nmap_vuln_node = NMAPVulnNode('9','nmap_vuln',nmap_vuln_parameters)


    machine_check_node = ChatGPTNode(
        node_id="10",
        name="Machine Checker",
        parameters={
            "api_key": "OPENAI_API_KEY",
            "model": "gpt-3.5-turbo",
            "prompt": lib.prompt.machine_checker
        }
    )


    os_nmap_parameters = {
        "ip": ip,
        "port": "22, 445",
        "option": "-O --fuzzy"
    }
    os_nmap_node = NmapNode('11', 'os_nmap', os_nmap_parameters)


    smb_mount_node = SMBMountNode(
        node_id="1", 
        name="SMB Enumeration and Mount Node", 
        parameters={
            "input_file": "./results/SMB_Cracker_Result.json"
        }
        )


    report_generate_node = ChatGPTNode(
        node_id="99",
        name="ReportGenerate",
        parameters={
            "api_key": "OPENAI_API_KEY",
            "model": "gpt-3.5-turbo",
            "prompt": lib.prompt.report_generate
        }
    )

    # Nodes' map
    nodes = {
        "1": ping1,
        "2": initial_nmap_node,
        "3": smb_nmap_node,
        "4": smbclient_node,
        "5": ftp_anonymous_node,
        "6": banner_node,
        "7": chat_node,
        "8": blue_node,
        "9": nmap_vuln_node,
        "10": machine_check_node,
        "11": os_nmap_node,
        "12": smb_mount_node,
        "99": report_generate_node
    }
    return nodes
