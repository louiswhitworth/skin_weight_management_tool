import maya.cmds as cmds
import re

#Sets maximum number of influencing joint per vertex on any selection of meshes or vertices based on user input in UI.
def set_max_joints(*args):
    max_joint_input = cmds.intField("input_number", v=True, q=True)
    selection = cmds.ls(sl=True)

    if not selection:
        cmds.error("Selection is empty.")

    #Check that selection is contains either only meshes or only vertices
    for sel in selection:
        is_transform = cmds.objectType(sel, i="transform")
        is_vertex = ".vtx" in sel
        if not is_transform and not is_vertex:
            cmds.error("Selection must either be a mesh or vertices")
        
    #Set max joint influence on mesh objects
    if is_transform:
        print("Removing influence from mesh")
        for sel in selection:
            #Get skin cluster and vertices for geometry. Check if mesh is skinned object
            geo_history = cmds.listHistory(sel, pdo=True)
            skin_cluster_list = cmds.ls(geo_history, type="skinCluster") or [None]
            skin_cluster = skin_cluster_list[0]
            
            if not skin_cluster:
                cmds.error("No skin cluster attached to mesh.")

            vertices = cmds.ls(f"{sel}.vtx[*]", flatten=True)

            remove_joint_influence_over_max(vertices, max_joint_input, skin_cluster)
    
    #Set max joint influence on mesh objects
    elif is_vertex:
        print("Removing influence from vertex")
        #Parse maya multi string selection into full list
        all_vertices = parse_stupid_maya_vert_strings(selection)
        
        #Get skin cluster and geometry from verices. Check if mesh is skinned object
        mesh = selection[0].split(".")[0]
        geo_history = cmds.listHistory(mesh, pdo=True)
        skin_cluster_list = cmds.ls(geo_history, type="skinCluster") or [None]
        skin_cluster = skin_cluster_list[0]
        
        if not skin_cluster:
            cmds.error("No skin cluster attached to mesh.")
                
        remove_joint_influence_over_max(all_vertices, max_joint_input, skin_cluster)

    else:
        print("is neither")

#Parse maya multi vertice string into full list of all selected vertices. Needed for cmds.skinPerecent commands. 
def parse_stupid_maya_vert_strings(vertices_list: str):

    all_selected_vertex = []

    for sublist in vertices_list:
        # check if it is the single vertex or list of vertices
        if ':' in sublist:
            indeces = use_regex(sublist)
            object_name = sublist.split('.')[0]
            for i in range(int(indeces[0]), int(indeces[1])+1):
                # 
                all_selected_vertex.append(f'{object_name}.vtx[{i}]')
        else:
            all_selected_vertex.append(sublist)

    return all_selected_vertex


# Regex to get the digits. Don't ask. 
def use_regex(input_text):
    pattern = re.compile(r"\[[^\]]*\]", re.IGNORECASE)
    return pattern.findall(input_text)[0][1:-1].split(':')

#Per vertex, sorts joint weight and removes smallest joint weights over max value from user input.
def remove_joint_influence_over_max(vertices, max_joints, skin_cluster):   
    for vertex in vertices:
        #Get joint influences for vertex
        influences = cmds.skinPercent(skin_cluster, vertex, q=True, t=None)
        
        #Check if num of influences is greater than user input. 
        if len(influences) > max_joints:
            #Get and sort joint weights in descending order by weight value. 
            weights = cmds.skinPercent(skin_cluster, vertex, q=True, v=True)
            joint_weights = list(zip(influences, weights))
            joint_weights.sort(key=lambda L: L[1], reverse=True)
            
            #Use max_joints to determine which joints influence to prune from the vertex
            #keep_weights = joint_weights[:max_joints]
            prune_weights = joint_weights[max_joints:]
            for influence, weight in prune_weights:
                cmds.skinPercent(skin_cluster, vertex, transformValue=[(influence, 0)])
            
            #Normalize remaining joint influence
            cmds.skinPercent(skin_cluster, vertex, normalize=True)

    print(f"Joint influence succesfully limited to {max_joints}")

#Create tool UI
def remove_joints_over_max_tool_ui():
    #Check if the window exists, and if it does, delete

    if(cmds.window("remove_joints_over_max_tool_ui", ex=1)):
        cmds.deleteUI("remove_joints_over_max_tool_ui")

    #Create window
    window = cmds.window("remove_joints_over_max_tool_ui", t="Remove joint influences of set number for each vertice on each selected object.", w=200, h=25, s=0)

    #Create the main layout
    mainLayout = cmds.formLayout(nd=100)

    #Buttons
    set_max_joints_button = cmds.button(l="Apply Max Joints", c=set_max_joints)
    
    #Input field
    max_joint_input = cmds.intField("input_number", min = 1, v = 1)
    text = cmds.text(label="Max Number of Influencing Joints: ")
    

    #Adjust layout
    cmds.formLayout(mainLayout, e=1, attachForm=[
                                                 (text, 'top', 5), (text, 'left', 5),
                                                 (max_joint_input, 'right', 5), (max_joint_input, 'top', 5),
                                                 (set_max_joints_button, 'left', 5), (set_max_joints_button, 'right', 5), (set_max_joints_button, 'bottom', 5)
                                                 ],
                                                      
                                    attachControl=[
                                                (set_max_joints_button, 'top', 5, max_joint_input)
                                                ]

                                                 )

    #Display window
    cmds.showWindow(window)
    