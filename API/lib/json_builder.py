import json

def organize_results_by_ip(input_file: str, output_file: str = './results/result_by_ip.json'):
    # Define the node names corresponding to their number codes
    nodes = {
        "1": "ping1",
        "2": "initial_nmap_node",
        "3": "smb_nmap_node",
        "4": "smbclient_node",
        "5": "ftp_anonymous_node",
        "6": "banner_node",
        "7": "chat_node",
        "8": "blue_node",
        "9": "smb_vuln_node",
        "10": "machine_check_node",
        "11": "os_nmap_node",
        "12": "smb_mount_node"
    }

    # Read the input JSON file
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Dictionary to store results by IP address
    results_by_ip = {}

    # Iterate over the original data
    for node_number, node_content in data.items():
        if "success" in node_content:
            for ip, success_data in node_content["success"].items():
                # Initialize the IP entry if it doesn't exist
                if ip not in results_by_ip:
                    results_by_ip[ip] = {node_name: None for node_name in nodes.values()}

                # Get the corresponding node name
                node_name = nodes.get(node_number, f"unknown_node_{node_number}")

                # Add the success data under the appropriate node name for the IP
                results_by_ip[ip][node_name] = success_data

    # Write the organized results to the output file
    with open(output_file, 'w') as output_file:
        json.dump(results_by_ip, output_file, indent=4)

    print(f"Results have been saved to {output_file}")

# Example usage
#organize_results_by_ip('./results/filtered_results.json')
