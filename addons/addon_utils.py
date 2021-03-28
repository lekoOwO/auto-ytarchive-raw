import re
import random 
import os
import mimetypes

import const

if const.BROTLI_COMPRESS:
    import brotli
    import tempfile
 
def read_file_as_content(filename): 
  #print filename 
  try: 
    with open(filename, 'rb') as f: 
      filecontent = f.read() 
  except Exception as e: 
    print('The Error Message in read_file_as_content(): ' + e.message)  
    return ''
  return filecontent 
 
 
def get_content_type(filename): 
  return mimetypes.guess_type(filename)[0] or 'application/octet-stream' 
 
def is_file_data(p_str):  
  rert = re.search("^f'(.*)'$", p_str) 
  if rert: 
    return rert.group(1) 
  else: 
    return None 
   
def encode_multipart_formdata(fields):
  BOUNDARY = f"----------{''.join(random.sample('0123456789abcdef', 15))}"
  CRLF = b'\r\n'
  
  L = [] 
  for (key, value) in fields: 
    filepath = is_file_data(value) 
    if filepath: 
      L.append(f'--{BOUNDARY}'.encode()) 
      L.append(f'Content-Disposition: form-data; name="{key}"; filename="{os.path.basename(filepath)}"'.encode()) 
      L.append(f'Content-Type: {get_content_type(filepath)}'.encode()) 
      L.append(''.encode()) 
      L.append(read_file_as_content(filepath))  
    else: 
      L.append(f'--{BOUNDARY}'.encode()) 
      L.append(f'Content-Disposition: form-data; name="{key}"'.encode()) 
      L.append(''.encode()) 
      L.append(value.encode())  
  L.append(f'--{BOUNDARY}--'.encode()) 
  L.append(''.encode())

  body = CRLF.join(L) 
  content_type = f'multipart/form-data; boundary={BOUNDARY}'
  return content_type, body
  
def compress_file(file):
    with open(file, encoding="utf8") as f:
        compressor = brotli.Compressor(mode=brotli.BrotliEncoderMode.TEXT)
        with tempfile.NamedTemporaryFile(prefix=(os.path.basename(file)+"."), suffix=".br", delete=False) as l:
            for line in f:
                data = line.encode()
                data = compressor.compress(data)
                l.write(compressor.flush())
            l.write(compressor.finish())
            return l.name