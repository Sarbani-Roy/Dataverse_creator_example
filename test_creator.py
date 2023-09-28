from pyDataverse.api import NativeApi
from pyDataverse.models import Dataverse
from pyDataverse.utils import read_file
import json
from requests import post

BASE_URL = "https://demodarus.izus.uni-stuttgart.de"
API_TOKEN = ""
DV_PARENT_ALIAS = "roy_dataverse"

def find_highest_continuous_match(string1, string2):
    # Initialize variables
    m = len(string1)
    n = len(string2)
    max_length = 0
    end_index = 0

    # Create a matrix to store the lengths of common substrings
    matrix = [[0] * (n + 1) for _ in range(m + 1)]

    # Iterate over the strings and fill the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if string1[i - 1] == string2[j - 1]:
                matrix[i][j] = matrix[i - 1][j - 1] + 1
                if matrix[i][j] > max_length:
                    max_length = matrix[i][j]
                    end_index = i

    # Extract the highest continuous match substring
    match = string1[end_index - max_length: end_index]

    return match



def find_max_match(dataverse_alias, parent_dv_alias, dv_creation_position, max_match, max_match_alias):
    childern_dv = api.get_children(parent_dv_alias)

    for child_dv in childern_dv:
        child_dv_alias = child_dv["dataverse_alias"]
        match = find_highest_continuous_match(child_dv_alias, dataverse_alias)
        if match == dataverse_alias:
            print("Dataverse " + dataverse_name + " already exists.")
            max_match_alias = ""
            break
        else:
            if len(match) > max_match:
                max_match = len(match)
                max_match_alias = child_dv_alias
                dv_creation_position = parent_dv_alias

                # Check if the current dataverse has any nested children
                nested_children_dv = api.get_children(child_dv_alias)
                if nested_children_dv:
                    dv_creation_position, max_match, max_match_alias = find_max_match(dataverse_alias, child_dv_alias, dv_creation_position, max_match, max_match_alias)

    return dv_creation_position, max_match, max_match_alias


# Function to assign admin role to a dataverse
def assign_role_to_dataverse(dv_alias, credentials, role_definition):
    #role_definition = {"assignee": "@fangfang.wang", "role": "admin"}
  
    if not ("assignee" in role_definition and "role" in role_definition):
        print("Error in Role Definition")
        return None

    query_str = '/dataverses/{}/assignments'.format(dv_alias)
    resp = post('{}/api{}'.format(credentials['base_url'], query_str), headers={'X-Dataverse-Key': credentials['api_key'], 'Content-type': 'application/json'}, data=json.dumps(role_definition))
    
    if resp.status_code == 200:
        print("New Role to DV {}: {}".format(dv_alias, json.dumps(role_definition)))
    else:
        print("Error assigning role: ", resp.status_code, resp.text)
        return False
    return resp.json()


api = NativeApi(BASE_URL, API_TOKEN)

dv = Dataverse()
dv_filename = "multiple_dataverse.json"

# Load the JSON data from the file
with open(dv_filename, 'r') as file:
    data = json.load(file)

single_dataverse = ""

for block in data:
    
    single_dataverse_file = "single_dataverse.json"
    dataverse_name = block.get("name")
    dataverse_alias = block.get("alias")
    
    fields_to_save = {
        "name": dataverse_name,
        "alias": dataverse_alias,
        "dataverseContacts": block.get("dataverseContacts"),
    }

    # Save the fields into the output_file
    with open(single_dataverse_file, "w") as file:
        json.dump(fields_to_save, file)

    dv.from_json(read_file(single_dataverse_file))

    dv_creation_position = DV_PARENT_ALIAS
    max_match = 0
    max_match_alias = ""

    dv_creation_position, max_match, max_match_alias = find_max_match(dataverse_alias, dv_creation_position, DV_PARENT_ALIAS, max_match, max_match_alias)
    
    # Creating the dataverse and publish it if does not exists
    if max_match_alias:
        resp_create = api.create_dataverse(dv_creation_position, dv.json())
    
    resp_publish = api.publish_dataverse(dataverse_alias)

    # Extract the role definition and save it into role_definition.json
    dataverse_role = block.get("role_definition")
    for role in dataverse_role:
        credentials = {'base_url': BASE_URL, 'api_key': API_TOKEN}
        assign_role_to_dataverse(dataverse_alias, credentials, role)