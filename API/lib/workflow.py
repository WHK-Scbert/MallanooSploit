from lib.nodes import Workflow

RESULT_DIR = "./results"

def SMBCraker_Builder(nodes):
    SMB_Cracker_wf = Workflow(output_file=RESULT_DIR+'/SMB_Cracker_result.json')
    SMB_Cracker_wf.add_nodes_by_id(nodes, ['9','4','8'])
    SMB_Cracker_wf.connect_nodes('9','4')
    SMB_Cracker_wf.connect_nodes('4','8')
    return SMB_Cracker_wf


def FTPAnonymousCheck_Builder(nodes):
    FTP_Anonymous_wf = Workflow(output_file=RESULT_DIR+'/FTP_Annonymous_result.json')
    FTP_Anonymous_wf.add_nodes_by_id(nodes, ['5','6','10'])
    FTP_Anonymous_wf.connect_nodes('5','6')
    FTP_Anonymous_wf.connect_nodes('6','10')
    return FTP_Anonymous_wf

def WebScanCheck_Builder(nodes):
    WebscanCheck_wf = Workflow(output_file=RESULT_DIR+'/WebScanCheck_result.json')
    WebscanCheck_wf.add_nodes_by_id(nodes, ['5','6','10'])
    WebscanCheck_wf.connect_nodes('5','6')
    WebscanCheck_wf.connect_nodes('6','10')
    return WebscanCheck_wf