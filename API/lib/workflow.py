from lib.nodes import Workflow

def SMBCraker_Builder(nodes):
    SMB_Cracker_wf = Workflow()
    SMB_Cracker_wf.add_nodes_by_id(nodes, ['3','4','8'])
    SMB_Cracker_wf.connect_nodes('3','4')
    SMB_Cracker_wf.connect_nodes('4','8')
    return SMB_Cracker_wf


