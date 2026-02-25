import os
bp = r"Z:\MAPA DEL DELITO\MAPAS DEL DELITO POR JURISDICCIONES"
print("Z: existe:", os.path.exists("Z:\\"))
print("Base path existe:", os.path.exists(bp))
if os.path.exists(bp):
    items = os.listdir(bp)
    print(f"Total carpetas/archivos: {len(items)}")
    for x in items[:20]:
        print(f"  - {x}")
else:
    print("NO ACCESIBLE - la unidad Z: puede no estar mapeada")
