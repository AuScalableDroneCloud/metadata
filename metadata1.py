#
# writes an image file and updated the metadata parameter - description text value
#

import requests
import os
import json
from datetime import datetime

print("Start...")

collectionId = "80194"
collectionFolder = "/chris_16SEP2022"

#Try to get REST credentials
filename = "login.json"
try:
    with open(filename) as f:
        user_details = json.load(f)
        username = user_details.get("username")
        password = user_details.get("password")
except:
    print("Exception - login.json")
    raise

auth = requests.auth.HTTPBasicAuth( username, password )
headers_object = {"Accept":"application/json"}

# get collection metadata

url = "https://daptst.csiro.au/dap/api/v2/collections/"+collectionId
r = requests.get(url, auth=auth)
if r.ok:
    print("GET collection metadata completed successfully!")
else:
    print("Something went wrong!")
metadata = r.json()
new_metadata = metadata.copy()  #Copy the metadata dict.


print(json.dumps(new_metadata, indent=2))

#metada.json
# {'name': 'Structural Geology', 'description': 'Fracture detection with Complex Shearlet Transform based on https://github.com/rahulprabhakaran/Automatic-Fracture-Detection-Code Using the Python port of the Matlab Toolbox Complex Shearlet-Based Ridge and Edge Measurement by Rafael Reisenhofer: https://github.com/rgcda/PyCoShREM', 'notebook': {'file': 'CoSh_ensemble_webodm.ipynb', 'version': 1.0, 'parameters': {'waveletEffSupp': 60.0, 'gaussianEffSupp': 20.0, 'scalesPerOctave': 4.0, 'shearLevel': 3.0, 'alpha': 0.2, 'octaves': 3.5, 'minContrast': 5.6, 'offset': 1.2, 'scalesUsedForPivotSearch': 1.0, 'min pixel value': 1.0, 'kernel size': 1024, 'min cluster size': 4098}, 'assets': [{'type': 'input', 'description': '', 'name': 'orthomosaic', 'format': 'tif'}, {'type': 'output', 'description': '', 'name': 'polyFile', 'format': 'shp'}, {'type': 'output', 'description': 'edge graph dot file', 'name': 'graph.dot', 'format': 'dot'}, {'type': 'output', 'description': 'A even-symmetric real-valued shearlet', 'name': 'fracture.png', 'format': 'png'}]}, 'author': 'Uli Kelka', 'organisation': 'CSIRO ', 'licence': {'name': 'It is distributed under BSD 3-Clause License'}, 'run': {'date': '15 September 2022', 'duration': 36000}}

filename = "metadata.json"
try:
    with open(filename) as f:
        metadata = json.load(f)
except:
    print("Exception - metadata.json")
    raise

new_metadata["description"] = metadata.get("description")
new_metadata["credit"] = metadata.get("author")
notebook = metadata.get("notebook")
new_metadata["lineage"] = "notebook:"+notebook.get("file")+"\nversion:"+str(notebook.get("version"))+"\nparameters: "+str(notebook.get("parameters"))
print(json.dumps(new_metadata, indent=2))
save_request = requests.put(url,
    auth=auth,
    headers=headers_object,
    json=new_metadata)
print("Response code: {0}".format(save_request.status_code))

#print(metadata.get("name"))
notebook = metadata.get("notebook")
assets = notebook.get("assets")
index = 0
files = []
old_type = ""
print(len(assets))
writeFiles = False
for asset in assets:
   index = index +  1
   print("*** asset '{0}' '{1}'".format(index,asset))
   filename = asset.get("name")
   type = asset.get("type")
   if (type == old_type) or (old_type == ""):
      print(str(index)+": "+type+" - "+filename)
      files.append( ('file',(os.path.split(filename)[1],open(filename,'rb')) ) )
   else:
      url = "https://daptst.csiro.au/dap/api/v2/collections/"+collectionId+"/files?path=/"+old_type
      writeFiles = True

   if (index == len(assets)) and not(writeFiles):
      url = "https://daptst.csiro.au/dap/api/v2/collections/"+collectionId+"/files?path=/"+type
      writeFiles = True
   if writeFiles: 
      print(files)
      print(url)
      r = requests.post(url, auth=auth, files=files)
      if r.ok:
         print("Upload completed successfully!")
         print(r.text)
      else:
         print("FILES: Something went wrong!")
         print(r.text)
      files = []
      files.append( ('file',(os.path.split(filename)[1],open(filename,'rb')) ) )
      writeFiles = False
   old_type = type

#
#https://confluence.csiro.au/display/dap/Update+and+publish+a+new+version+of+a+collection+-+API+V2
#
#If you wish to add or modify file level metadata, this requires two API calls.  Note that most DAP user's don't add file level metadata, and several image file formats will have EXIF metadata automatically extracted where possible.
#Send a GET request to /api/v2/collections/{new_dataCollectionId}/file?path={url_encoded_path_to_folder_AND_file_name} , e.g. ...?path=%2Ffile_in_root_folder.txt . This will return metadata for the file.
#From the response get the "id" value from the file metadata.  This page will refer to the "id" value as "file_id".
#Modify the "parameters" list in the response. (TODO: this requires an entire page of its own)
#Send a PUT request to /api/v2/collections/{new_dataCollectionId}/files/{file_id} .

index = 0
for asset in assets:
   filename = asset.get("name")
   type = asset.get("type")
   collectionFolder = "/"+type
   url = "https://daptst.csiro.au/dap/api/v2/collections/"+collectionId+"/file?path="+collectionFolder+"/"+os.path.split(filename)[1]
   print("filename:"+os.path.split(filename)[1])
   print("add metadata to "+collectionFolder+"/"+os.path.split(filename)[1])
   r = requests.get(url, auth=auth)
   if r.ok:
       print("GET metadata completed successfully!")
   else:
       print("Something went wrong!")

   metadata = r.json()
   fileId = metadata.get("id")
   if not fileId:
       print("ERROR: POST request to '{0}' ".format(url) \
           + "did not contain a fileId in the response.")
       #You would need some error handling here.
   print("fileId: {0}".format(fileId))

   params = metadata.get("parameters")
   print(json.dumps(params, indent=2))

   #metadata["parameters"] = [{"title": "test by chris" } ]
   # params[].{name:Description, StringValue:}
   index=0
   for param in params:
     print("*** param '{0}' '{1}'".format(index,param))
     if param.get("name") == "Title":
       param["stringValue"] =  "Structural Geology"
       params[index] = param
     if param.get("name") == "Creator":
       sv = param.get("stringValue")
       param["stringValue"] = sv
       params[index] = param
     if param.get("name") == "Creation Date":
       param["stringValue"] = datetime.now().strftime("%Y-%m-%d")
       params[index] = param
     if param.get("name") == "Description":
       param["stringValue"] = asset.get("description")
       params[index] = param
     if param.get("name") == "Format":
       param["stringValue"] = asset.get("format")
       params[index] = param
     if param.get("name") == "Coverage":
       param["stringValue"] = "coverage"
       params[index] = param
     if param.get("name") == "Source":
       param["stringValue"] = "source"
       params[index] = param
     if param.get("name") == "Subject":
       param["stringValue"] = "rock fracture"
       params[index] = param
     if param.get("name") == "Identifier":
       param["stringValue"] = "identifier"
       params[index] = param
     index = index + 1

   metadata["parameters"] = params
   print(json.dumps(metadata, indent=2))

   url = "https://daptst.csiro.au/dap/api/v2/collections/"+collectionId+"/files/{0}".format(fileId)
   print("PUT url '{0}'".format(url))

   save_request = requests.put(url,
       auth=auth,
       headers=headers_object,
       json=metadata)
 
   print("Response code: {0}".format(save_request.status_code))

print("...End")
