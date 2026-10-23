"""Exporta cada diapositiva de un .pptx a PNG con PowerPoint (COM)."""
import sys, os, glob
import win32com.client
pptx_path = os.path.abspath(sys.argv[1]); out_dir = os.path.abspath(sys.argv[2])
width = int(sys.argv[3]) if len(sys.argv) > 3 else 1600
os.makedirs(out_dir, exist_ok=True)
for f in glob.glob(os.path.join(out_dir, "*.png")): os.remove(f)
app = win32com.client.Dispatch("PowerPoint.Application")
pres = app.Presentations.Open(pptx_path, ReadOnly=True, Untitled=False, WithWindow=False)
n = pres.Slides.Count
for i in range(1, n + 1):
    pres.Slides(i).Export(os.path.join(out_dir, f"s{i:02d}.png"), "PNG", width, int(width * 9 / 16))
pres.Close()
try:
    if app.Presentations.Count == 0: app.Quit()
except Exception: pass
print(f"exportadas {n} diapositivas a {out_dir}")
