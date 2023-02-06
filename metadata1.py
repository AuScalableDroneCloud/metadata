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
    print("error reading login.json")
    exit()

print("username: "+username)

auth = requests.auth.HTTPBasicAuth( username, password )
headers_object = {"Accept":"application/json"}
# get collection metadata
url = "https://daptst.csiro.au/dap/api/v2/collections/"+collectionId
#url = "https://152.83.245.5/dap/api/v2/collections/"+collectionId
#url = "https://138.194.81.130/dap/api/v2/collections/"+collectionId
#url = "https://150.229.21.85/dap/api/v2/collections/"+collectionId
try:
    r = requests.get(url, auth=auth)
    print("requests")
    if r.ok:
        print("Collection "+collectionId+" metadata accessed")
    else:
        print("Something went wrong!")

except requests.exceptions.Timeout:
    # Maybe set up for a retry, or continue in a retry loop
    print("retry...")
except requests.exceptions.TooManyRedirects:
    # Tell the user their URL was bad and try a different one
    print("bad url..")
except requests.exceptions.RequestException as e:
    # catastrophic error. bail.
    raise SystemExit(e)

metadata = r.json()
new_metadata = metadata.copy()  #Copy the metadata dict.
print(json.dumps(new_metadata, indent=2))

#metada.json
filename = "metadata.json"
try:
    with open(filename) as f:
        metadata = json.load(f)
except:
    print("Exception - metadata.json")
    raise

new_metadata["collectionContentTypeCode"] = "D"
new_metadata["description"] = metadata.get("description")
new_metadata["credit"] = metadata.get("author")
new_metadata["keywords"] = "drone;geology;asdc"
notebook = metadata.get("notebook")
#new_metadata["lineage"] = "notebook:"+notebook.get("file")+"\nversion:"+str(notebook.get("version"))+"\nparameters: "+str(notebook.get("parameters"))
#new_metadata["lineage"] = "notebook:"+notebook.get("file")+"\nversion:"+str(notebook.get("version"))+"\nparameters: refer to the file input/params.json" 
new_metadata["lineage"] = "notebook:"+notebook.get("file")+"\nversion:"+str(notebook.get("version"))+"\nparameters: refer to the file input/params.json\nsensor: refer to the file sensor/sensor.json\nrefer to the file spatial/spatial.json"

#new_metadata["spatialParameters"] = { "projection": "GDA94", "northLatitude": "-31.147592777777778", "southLatitude": "-31.285619722222226", "westLongitude": "134.0348586111111", "eastLongitude": "134.17288555555555" }
geoRef = notebook.get("Georeference info")
proj = geoRef[0].get("Projection")
bounds = geoRef[0].get("Bounding Coodinates")
new_metadata["spatialParameters"] = { "projection": "GDA94", "northLatitude": bounds[1][0], "southLatitude": bounds[0][0], "westLongitude": bounds[1][1], "eastLongitude" : bounds[0][1] }

# create sensor.json file - for upload
sensorRef = geoRef[0].get("Image metadata")
#print("sensor: "+json.dumps(sensorRef))
with open('data/sensor.json', 'w', encoding='utf-8') as f:
    json.dump(json.dumps(sensorRef), f, ensure_ascii=False, indent=4)
sensorFile = { "type": "sensor", "title": "Structural Geology", "creator": "Uli Kelka", "description": "sensor metadata file", "name": "data/sensor.json", "format": "json" }

# create spatial.json file - for upload
#print("geoRef: "+json.dumps(geoRef))
#print("spatial.projection : "+json.dumps(proj))
#print(proj)
spatialRef = { "projection" : proj, "bounds" : bounds }
with open('data/spatial.json', 'w', encoding='utf-8') as f:
    json.dump(json.dumps(spatialRef), f, ensure_ascii=False, indent=4)
spatialFile = { "type": "spatial", "title": "Structural Geology", "creator": "Uli Kelka", "description": "spatial metadata file", "name": "data/spatial.json", "format": "json" }

#print(json.dumps(new_metadata, indent=2))
save_request = requests.put(url,
    auth=auth,
    headers=headers_object,
    json=new_metadata)
#print("Response code: {0}".format(save_request.status_code))

# create params.json file - for upload
with open('data/params.json', 'w', encoding='utf-8') as f:
    json.dump(notebook.get("parameters"), f, ensure_ascii=False, indent=4)
paramFile = { "type": "input", "title": "Structural Geology", "creator": "Uli Kelka", "description": "parameters file", "name": "data/params.json", "format": "json" }

#print(metadata.get("name"))
notebook = metadata.get("notebook")
assets = notebook.get("assets")
assets.append(paramFile)
assets.append(sensorFile)
assets.append(spatialFile)

url = "https://daptst.csiro.au/dap/api/v2/collections/"+collectionId+"/files/unlock"
r = requests.post(url, auth=auth, headers=headers_object)
if not r.ok:
   print("unlock: Something went wrong!")
   print(r.text)

i = 1
unlocked = False
while (i < 10000) and (not unlocked):
   url = "https://daptst.csiro.au/dap/api/v2/collections/"+collectionId+"/files/fileState"
   try:
       r = requests.get(url, auth=auth)
       if r.ok:
           print(r.text);
           print("Collection "+collectionId+" unlocked")
           if r.text == "unlocked":
              print("set unlocked")
              unlocked = True
       else:
           print("GET: Something went wrong!")

   except requests.exceptions.Timeout:
       # Maybe set up for a retry, or continue in a retry loop
       print("retry...")
   except requests.exceptions.TooManyRedirects:
       # Tell the user their URL was bad and try a different one
       print("bad url..")
   except requests.exceptions.RequestException as e:
       # catastrophic error. bail.
       raise SystemExit(e)
   i+=1



index = 0
files = []
old_type = ""
print("Uploading "+str(len(assets))+" assets...")
writeFiles = False
ts = datetime.now().strftime("%d%b%Y_%H%M")
#print("timestamp: "+ts)
baseURL = "https://daptst.csiro.au/dap/api/v2/collections/"+collectionId+"/files?path=/"+ts+"/"

# upload the assets - files
"""
for asset in assets:
   index = index +  1
   print("\n*** asset '{0}' '{1}'".format(index,asset))
   filename = asset.get("name")
   type = asset.get("type")
   print("\t"+str(index)+": "+type+" - "+filename)

   if (type == old_type) or (old_type == ""):
      print("[if stmt] "+str(index)+": "+type+" - "+filename)
      files.append( ('file',(os.path.split(filename)[1],open(filename,'rb')) ) )
   else:
      print("[else]")
      if (index != len(assets)) and not(writeFiles):
         url = baseURL + old_type
         files.append( ('file',(os.path.split(filename)[1],open(filename,'rb')) ) )
         writeFiles = True

   if (index == len(assets)) and not(writeFiles):
      print("[last asset]")
      url = baseURL + type
      writeFiles = True

   if writeFiles: 
      print("[writeFiles]")
      print(files)
      print(url)
      r = requests.post(url, auth=auth, files=files)
      if not r.ok:
         print("FILES: Something went wrong!")
         print(r.text)
      files = []
      files.append( ('file',(os.path.split(filename)[1],open(filename,'rb')) ) )
      writeFiles = False
   old_type = type
"""

# upload the assets - files
for asset in assets:
   index = index +  1
   print("\n*** asset '{0}' '{1}'".format(index,asset))
   filename = asset.get("name")
   type = asset.get("type")
   print("\t"+str(index)+": "+type+" - "+filename)

   url = baseURL + type
   files.append( ('file',(os.path.split(filename)[1],open(filename,'rb')) ) )
   r = requests.post(url, auth=auth, files=files)
   if not r.ok:
      print("FILES: Something went wrong!")
      print(r.text)
   files = []

# add metadata for each of the files(assets)  uploaded previously
index = 0
print("\nAdding metadata to asset:")
for asset in assets:
   filename = asset.get("name")
   type = asset.get("type")
   collectionFolder = "/"+ts+"/"+type
   url = "https://daptst.csiro.au/dap/api/v2/collections/"+collectionId+"/file?path="+collectionFolder+"/"+os.path.split(filename)[1]
   print("\t"+collectionFolder+"/"+os.path.split(filename)[1])
   r = requests.get(url, auth=auth)
   if not r.ok:
       print("Something went wrong!")

   metadata = r.json()
   print(json.dumps(metadata, indent=2))
   fileId = metadata.get("id")
   if not fileId:
       print("ERROR: POST request to '{0}' ".format(url) \
           + "did not contain a fileId in the response.")
       #You would need some error handling here.
   #print("fileId: {0}".format(fileId))

   params = metadata.get("parameters")
   #print(json.dumps(params, indent=2))

   #metadata["parameters"] = [{"title": "test by chris" } ]
   # params[].{name:Description, StringValue:}
   index=0
   # if no params (typically if not an image file), need to add at least title and creator fields
   if (len(params) == 0):
      params.append( { "name": "Title", "dateValue": "", "dateValueString": "", "numericValue": "", "stringValue": "" } )
      params.append( { "name": "Creator", "dateValue": "", "dateValueString": "", "numericValue": "", "stringValue": "" } )
      params.append( { "name": "Description", "dateValue": "", "dateValueString": "", "numericValue": "", "stringValue": "" } )
   for param in params:
     #print("*** param '{0}' '{1}'".format(index,param))
     if param.get("name") == "Title":
       param["stringValue"] =  asset.get("title")
       params[index] = param
     if param.get("name") == "Creator":
       param["stringValue"] = asset.get("creator")
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
   #print("PUT url '{0}'".format(url))

   save_request = requests.put(url,
       auth=auth,
       headers=headers_object,
       json=metadata)
 
   #print("Response code: {0}".format(save_request.status_code))
   #print(save_request.text)


url = "https://daptst.csiro.au/dap/api/v2/collections/"+collectionId+"/validate"
print(url)
try:  
   r = requests.get(url, auth=auth)
   if r.ok:
       print(r.text);
       print("Collection "+collectionId+" validated")
   else:
       print("GET(validate): Something went wrong!")
except requests.exceptions.Timeout:
    # Maybe set up for a retry, or continue in a retry loop
    print("retry...")
except requests.exceptions.TooManyRedirects:
    # Tell the user their URL was bad and try a different one
    print("bad url..")
except requests.exceptions.RequestException as e:
    # catastrophic error. bail.
    raise SystemExit(e)


#print("...End")
