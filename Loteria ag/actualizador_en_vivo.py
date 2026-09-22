import json
import sys
import os
import webbrowser
from datetime import datetime

# Asegurar codificación UTF-8 en consola de Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_JSON = os.path.join(DIR_ACTUAL, "sorteos_hoy.json")
ARCHIVO_JS = os.path.join(DIR_ACTUAL, "datos_en_vivo.js")
ARCHIVO_HTML = os.path.join(DIR_ACTUAL, "index.html")

TABLA_JALADERA = {
    0: [78, 94, 89], 1: [46, 61, 99], 2: [68, 85, 86], 3: [23, 30, 74], 4: [20, 32, 44],
    5: [50, 55, 95], 6: [60, 66, 96], 7: [27, 72, 77], 8: [22, 88, 98], 9: [79, 90, 97],
    10: [56, 65, 80], 11: [36, 63, 81], 12: [26, 52, 62], 13: [53, 69, 73], 14: [18, 42, 64],
    15: [17, 45, 51], 16: [41, 47, 76], 17: [15, 45, 51], 18: [14, 42, 64], 19: [37, 43, 91],
    20: [4, 32, 44], 21: [25, 35, 70], 22: [8, 88, 98], 23: [3, 30, 74], 24: [34, 54, 84],
    25: [21, 35, 70], 26: [12, 52, 62], 27: [7, 72, 77], 28: [40, 58, 82], 29: [38, 59, 92],
    30: [3, 23, 74], 31: [48, 87], 32: [4, 20, 44], 33: [39, 83, 93], 34: [24, 54, 84],
    35: [21, 25, 70], 36: [11, 63, 81], 37: [19, 43, 91], 38: [29, 59, 92], 39: [33, 83, 93],
    40: [28, 58, 82], 41: [16, 47, 76], 42: [14, 18, 64], 43: [19, 37, 91], 44: [4, 20, 32],
    45: [15, 17, 51], 46: [1, 61, 99], 47: [41, 16, 76], 48: [31, 87], 49: [0, 94, 89],
    50: [5, 55, 95], 51: [15, 17, 45], 52: [12, 26, 62], 53: [13, 69, 73], 54: [24, 34, 84],
    55: [5, 50, 95], 56: [10, 65, 80], 57: [67, 71, 75], 58: [28, 40, 82], 59: [29, 38, 92],
    60: [6, 66, 96], 61: [1, 46, 99], 62: [12, 26, 52], 63: [11, 36, 81], 64: [14, 18, 42],
    65: [10, 56, 80], 66: [6, 60, 96], 67: [57, 71, 75], 68: [2, 85, 86], 69: [13, 53, 73],
    70: [21, 25, 35], 71: [75, 57, 67], 72: [7, 27, 77], 73: [13, 53, 69], 74: [3, 30, 23],
    75: [57, 71, 67], 76: [16, 41, 47], 77: [7, 27, 72], 78: [0, 94, 89], 79: [9, 90, 97],
    80: [10, 56, 65], 81: [11, 36, 63], 82: [28, 40, 58], 83: [33, 39, 93], 84: [24, 34, 54],
    85: [2, 68, 86], 86: [2, 68, 85], 87: [31, 48], 88: [8, 22, 98], 89: [0, 78, 94],
    90: [9, 79, 97], 91: [19, 37, 43], 92: [29, 38, 59], 93: [33, 39, 83], 94: [78, 0, 89],
    95: [5, 50, 55], 96: [6, 60, 66], 97: [9, 79, 90], 98: [8, 22, 88], 99: [1, 46, 61]
}

def cargar_datos():
    if os.path.exists(ARCHIVO_JSON):
        with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_datos(datos):
    # 1. Guardar JSON
    with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    
    # 2. Guardar JS para carga instantánea en navegador sin restricciones CORS
    with open(ARCHIVO_JS, "w", encoding="utf-8") as f:
        f.write("window.DATOS_LOTOPRO = " + json.dumps(datos, indent=2, ensure_ascii=False) + ";\n")
        
    print("✅ sorteos_hoy.json y datos_en_vivo.js actualizados con éxito.")

def registrar_sorteo(nombre_o_id, p1, p2, p3, abrir_navegador=True):
    datos = cargar_datos()
    sorteos = datos.get("sorteos_hoy", datos.get("sorteos", []))
    
    encontrado = None
    for s in sorteos:
        if nombre_o_id.lower() in s["nombre"].lower() or nombre_o_id.lower() in s["id"].lower():
            encontrado = s
            break
            
    if not encontrado:
        print(f"❌ No se encontró ningún sorteo que coincida con '{nombre_o_id}'.")
        print("Sorteos disponibles:")
        for s in sorteos:
            print(f" - {s['nombre']} ({s['hora']})")
        return False

    p1, p2, p3 = int(p1), int(p2), int(p3)
    encontrado["estado"] = "finalizado"
    encontrado["premios"] = [p1, p2, p3]
    
    jalados = TABLA_JALADERA.get(p1, [10, 20, 30])
    
    # Destino generalizado por tanda sin atar a loterías específicas
    tanda = encontrado.get("tanda", "")
    tanda_destino = "Elegibles con mayor atracción para la tanda de la TARDE y NOCHE" if tanda == "Mañana" else "Elegibles con mayor atracción para la tanda de la NOCHE"
    
    alerta = {
        "origen": encontrado["nombre"],
        "numero_disparador": int(p1),
        "jalados": jalados,
        "tanda_destino": tanda_destino,
        "nota": f"El {p1:02d} activa inercia de atracción para las jugadas de la tanda siguiente."
    }
    
    encontrado["alerta_cascada"] = alerta
    datos["alerta_cascada_activa"] = alerta
    
    ahora = datetime.now().strftime("%I:%M %p")
    datos["actualizado_a_las"] = ahora
    
    guardar_datos(datos)
    
    print("\n-----------------------------------------------------------")
    print(f"🎯 ¡RESULTADO REGISTRADO EN VIVO: {encontrado['nombre']}!")
    print(f"   Premios: [1RO: {p1:02d}]  [2DO: {p2:02d}]  [3RO: {p3:02d}]")
    print(f"⚡ EFECTO CASCADA ACTIVADO:")
    print(f"   El {p1:02d} jala a: {jalados}")
    print(f"   Destino: {tanda_destino}")
    print("-----------------------------------------------------------\n")
    
    if abrir_navegador:
        print("🌐 Abriendo el panel web en tu navegador...")
        webbrowser.open("file://" + ARCHIVO_HTML)
        
    return True

if __name__ == "__main__":
    if len(sys.argv) >= 5:
        # Uso: python actualizador_en_vivo.py "primera" 35 12 90
        sorteo = sys.argv[1]
        p1 = sys.argv[2]
        p2 = sys.argv[3]
        p3 = sys.argv[4]
        registrar_sorteo(sorteo, p1, p2, p3, abrir_navegador=True)
    else:
        # Modo interactivo paso a paso
        print("\n===========================================================")
        print("   LotoPro RD - PANEL DE ACTUALIZACIÓN EN VIVO")
        print("===========================================================\n")
        print("Sorteos de hoy:")
        print(" 1. Anguila 10 AM       4. Lotería Real 1:00 PM  7. Loteka 7:55 PM")
        print(" 2. La Primera 12:00 PM 5. Gana Más 2:30 PM      8. Leidsa 8:55 PM")
        print(" 3. La Suerte 12:30 PM  6. New York Tarde 2:30   9. Nacional Noche 9 PM")
        print("\nEjemplo de uso rápido por comando:")
        print('  python actualizador_en_vivo.py "primera" 35 12 90')
        print('  python actualizador_en_vivo.py "suerte" 48 15 22')
        print('  python actualizador_en_vivo.py "real" 54 80 11')
        print('  python actualizador_en_vivo.py "ganamas" 05 58 36')
        print("-----------------------------------------------------------\n")
        
        # Preguntar si desea abrir el panel web ahora mismo
        webbrowser.open("file://" + ARCHIVO_HTML)
        print("🌐 Panel web abierto en tu navegador.")
