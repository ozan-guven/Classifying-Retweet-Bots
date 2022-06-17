import bz2

filepath = "new_outputs/user_tweets/759251.jsonl.bz2"

zipfile = bz2.BZ2File(filepath)     # open the file
data = zipfile.read()               # get the decompressed data
newfilepath = filepath[:-4]         # assuming the filepath ends with .bz2
open(newfilepath, 'wb').write(data) # write a uncompressed file
