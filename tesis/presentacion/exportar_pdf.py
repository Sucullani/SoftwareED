"""Exporta un .pptx a PDF con PowerPoint (COM). Uso: python exportar_pdf.py entrada.pptx salida.pdf"""
import os
import sys

import win32com.client

src = os.path.abspath(sys.argv[1])
dst = os.path.abspath(sys.argv[2])
app = win32com.client.Dispatch("PowerPoint.Application")
pres = app.Presentations.Open(src, ReadOnly=True, Untitled=False, WithWindow=False)
pres.SaveAs(dst, 32)  # ppSaveAsPDF
pres.Close()
try:
    if app.Presentations.Count == 0:
        app.Quit()
except Exception:
    pass
print("PDF:", dst, round(os.path.getsize(dst) / 1e6, 2), "MB")
