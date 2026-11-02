import urllib.request,tarfile,io,pathlib,json
D=pathlib.Path(r'E:\.shortcut-targets-by-id\1yOBXNuSORBcOSWDhEg-YF1MEWIDvc8J2\Capstone- Inventory Management System\Dataset\external_candidates\wildreceipt')
u='https://download.openmmlab.com/mmocr/data/wildreceipt.tar'
req=urllib.request.Request(u,headers={'Range':'bytes=0-10485759'})
with urllib.request.urlopen(req,timeout=45) as r:
 print('range',r.status,r.headers.get('Content-Range'));data=r.read(10485761)
 if r.status!=206 or len(data)>10485760: raise ValueError('range unsupported; stopped')
(D/'range_metadata.json').write_text(json.dumps({'url':u,'range':'bytes=0-10485759','bytes_read':len(data)},indent=2))
t=tarfile.open(fileobj=io.BytesIO(data),mode='r:')
try:
 for m in t:
  print(m.name,m.size)
  if m.isfile() and m.size<6000000:
   p=D/m.name
   if not p.resolve().is_relative_to(D.resolve()):continue
   try:b=t.extractfile(m).read()
   except Exception:break
   p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
except tarfile.ReadError:pass

