#
# writes metadata to the DAP (daptst) as a draft to the exsiting collection id: 80194
# uses the REST credentials from login.json
# processes the metadata.json file
#

import requests
import os
import json
from datetime import datetime

print("Start...")

collectionId = "80194"

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
#print(json.dumps(new_metadata, indent=2))

#metada.json
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
#print(json.dumps(new_metadata, indent=2))
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

# add metadata for each of the files(assets)  uploaded previously
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
   #print(json.dumps(params, indent=2))

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
   #print(json.dumps(metadata, indent=2))

   url = "https://daptst.csiro.au/dap/api/v2/collections/"+collectionId+"/files/{0}".format(fileId)
   print("PUT url '{0}'".format(url))

   save_request = requests.put(url,
       auth=auth,
       headers=headers_object,
       json=metadata)
 
   print("Response code: {0}".format(save_request.status_code))

print("...End")
