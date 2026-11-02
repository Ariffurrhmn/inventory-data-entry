"""Flag perceptually similar images for review; candidates are not automatic duplicates."""
from PIL import Image
from prepare import HERE,read_csv,write_csv
def fingerprint(path):
 with Image.open(path) as im:
  pixels=list(im.convert("L").resize((9,8)).getdata())
 return sum((pixels[y*9+x]>pixels[y*9+x+1])<<(y*8+x) for y in range(8) for x in range(8))
def main():
 rows=read_csv(HERE/"data/manifest.csv");hashes=[fingerprint(HERE/r["image_path"]) for r in rows];pairs=[]
 for i,a in enumerate(rows):
  for j in range(i):
   distance=(hashes[i]^hashes[j]).bit_count()
   if distance<=6:pairs.append(dict(first=rows[j]["source_path"],second=a["source_path"],hamming_distance=distance,labels_match=rows[j]["label"]==a["label"]))
 write_csv(HERE/"data/duplicate_candidates.csv",pairs,["first","second","hamming_distance","labels_match"])
 print(f"{len(pairs)} perceptual candidates; inspect before splitting.")
if __name__=="__main__":main()
