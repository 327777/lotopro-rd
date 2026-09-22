import json
import os
import sys
import time
import ssl
import re
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime
from motor_jugada_maestra import calcular_jugada_maestra

# Asegurar codificación UTF-8 en consola de Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_JSON = os.path.join(DIR_ACTUAL, "sorteos_hoy.json")
ARCHIVO_JS = os.path.join(DIR_ACTUAL, "datos_en_vivo.js")

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
    with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    with open(ARCHIVO_JS, "w", encoding="utf-8") as f:
        f.write("window.DATOS_LOTOPRO = " + json.dumps(datos, indent=2, ensure_ascii=False) + ";\n")
    print("✅ Base de datos y archivo web actualizados exitosamente.")

def verificar_cambio_de_dia(datos):
    fecha_hoy_str = datetime.now().strftime("%Y-%m-%d")
    fecha_guardada = datos.get("fecha_hoy")
    
    if fecha_guardada and fecha_guardada != fecha_hoy_str:
        print(f"🌅 ¡Nuevo día detectado ({fecha_hoy_str})! Rotando sorteos de ayer y preparando la pizarra de hoy...")
        sorteos_ayer = []
        for s in datos.get("sorteos_hoy", []):
            if s.get("premios"):
                sorteos_ayer.append({
                    "nombre": s["nombre"],
                    "hora": s["hora"],
                    "premios": s["premios"]
                })
        if sorteos_ayer:
            datos["sorteos_ayer"] = sorteos_ayer
            
        for s in datos.get("sorteos_hoy", []):
            s["estado"] = "proximo"
            s["premios"] = None
            if "alerta_cascada" in s:
                del s["alerta_cascada"]
                
        datos["fecha_ayer"] = fecha_guardada
        datos["fecha_hoy"] = fecha_hoy_str
        nueva_pareja = calcular_jugada_maestra()
        if "jugada_maestra_fija" not in datos:
            datos["jugada_maestra_fija"] = {}
        datos["jugada_maestra_fija"]["pareja_oficial"] = nueva_pareja
        datos["actualizado_a_las"] = datetime.now().strftime("%I:%M %p")
        guardar_datos(datos)
        print(f"🎯 Nueva Jugada Maestra Matemática: {nueva_pareja[0]} - {nueva_pareja[1]}")
        print("✅ Pizarra de hoy reiniciada en limpio y sorteos de ayer archivados con éxito.")
        return True
    elif not fecha_guardada:
        datos["fecha_hoy"] = fecha_hoy_str
        guardar_datos(datos)
    return False

def hora_oficial_ha_pasado(hora_str):
    """
    CANDADO DE RELOJ:
    Verifica si la hora oficial del sorteo ya se cumplió según la hora local de RD.
    Si son las 4:50 PM y el sorteo es a las 7:55 PM, devuelve False (aún no se ha celebrado).
    """
    try:
        ahora = datetime.now()
        t = datetime.strptime(hora_str.strip(), "%I:%M %p")
        minutos_ahora = ahora.hour * 60 + ahora.minute
        minutos_sorteo = t.hour * 60 + t.minute
        return minutos_ahora >= minutos_sorteo
    except Exception:
        return True

def validar_fecha_tarjeta(texto_tarjeta):
    """
    CANDADO DE FECHA:
    Verifica que la tarjeta raspada de la web externa sea de HOY.
    Si la tarjeta dice '20/09/2026' y hoy es '21/09/2026', la rechaza categóricamente.
    """
    hoy = datetime.now()
    hoy_dmy = hoy.strftime("%d/%m/%Y")
    hoy_dmy_alt = f"{hoy.day}/{hoy.month}/{hoy.year}"
    
    fechas = re.findall(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", texto_tarjeta)
    if fechas:
        # Al menos una fecha de la tarjeta debe coincidir exactamente con hoy
        return any(f == hoy_dmy or f == hoy_dmy_alt for f in fechas)
    
    # Si la tarjeta no muestra fecha explícita, se apoya en el candado de reloj
    return True

def emparejar_sorteo(nombre_sorteo, hora_sorteo, texto_tarjeta):
    texto = texto_tarjeta.lower()
    nom = nombre_sorteo.lower()
    if "gana más" in nom or "gana mas" in nom:
        return ("gana" in texto or "2:30" in texto) and "nacional" in texto
    if "nacional" in nom:
        return "nacional" in texto and ("8:50" in texto or "9:00" in texto or "noche" in texto or "dark_mode" in texto)
    if "leidsa" in nom:
        return "leidsa" in texto
    if "real noche" in nom:
        return "real" in texto and ("noche" in texto or "9:00" in texto)
    if "quiniela real" in nom:
        return "real" in texto and ("12:55" in texto or "1:00" in texto or "brightness_high" in texto)
    if "lotedom" in nom:
        return "lotedom" in texto
    if "loteka" in nom:
        return "loteka" in texto
    if "primera noche" in nom:
        return "primera" in texto and ("8:00" in texto or "noche" in texto)
    if "primera día" in nom or "primera dia" in nom:
        return "primera" in texto and ("12:00" in texto or "día" in texto or "dia" in texto or "brightness_high" in texto)
    if "suerte tarde" in nom:
        return "suerte" in texto and ("6:00" in texto or "tarde" in texto)
    if "suerte día" in nom or "suerte dia" in nom:
        return "suerte" in texto and ("12:30" in texto or "día" in texto or "dia" in texto)
    if "new york tarde" in nom or "ny tarde" in nom:
        return ("new york" in texto or "ny" in texto) and ("tarde" in texto or "2:30" in texto)
    if "new york noche" in nom or "ny noche" in nom:
        return ("new york" in texto or "ny" in texto) and ("noche" in texto or "10:30" in texto)
    if "florida día" in nom or "florida dia" in nom:
        return "florida" in texto and ("día" in texto or "dia" in texto or "1:30" in texto)
    if "florida noche" in nom:
        return "florida" in texto and ("noche" in texto or "9:45" in texto)
    if "new jersey" in nom:
        return "jersey" in texto
    if "anguila" in nom:
        if "10:00" in nom or "10 am" in nom:
            return "anguila" in texto and "10:" in texto
        if "1:00" in nom or "1 pm" in nom:
            return "anguila" in texto and "1:" in texto
        if "6:00" in nom or "6 pm" in nom:
            return "anguila" in texto and "6:" in texto
        if "9:00" in nom or "9 pm" in nom:
            return "anguila" in texto and "9:" in texto
        return "anguila" in texto

    palabra = nom.replace("lotería", "").replace("quiniela", "").strip()
    return palabra in texto

def actualizar_historial_local(sorteo_id, premios):
    archivo_hist = os.path.join(DIR_ACTUAL, "historial_loterias.json")
    archivo_hist_js = os.path.join(DIR_ACTUAL, "datos_historial.js")
    hoy_str = datetime.now().strftime("%d/%m/%Y")
    
    if os.path.exists(archivo_hist):
        try:
            with open(archivo_hist, "r", encoding="utf-8") as f:
                hist = json.load(f)
            if sorteo_id in hist:
                if not any(r.get("fecha") == hoy_str for r in hist[sorteo_id]):
                    hist[sorteo_id].insert(0, {"fecha": hoy_str, "premios": premios})
                else:
                    for r in hist[sorteo_id]:
                        if r.get("fecha") == hoy_str:
                            r["premios"] = premios
                            break
                with open(archivo_hist, "w", encoding="utf-8") as f:
                    json.dump(hist, f, indent=2, ensure_ascii=False)
                with open(archivo_hist_js, "w", encoding="utf-8") as f:
                    f.write("window.HISTORIAL_LOTERIAS = " + json.dumps(hist, ensure_ascii=False) + ";\n")
                print(f"📁 Historial local sincronizado para {sorteo_id}.")
        except Exception as e:
            print(f"Aviso actualizando historial local: {e}")

def escanear_sorteos_en_vivo():
    print(f"[{datetime.now().strftime('%I:%M:%S %p')}] 📡 Escaneando resultados oficiales en vivo...")
    datos = cargar_datos()
    verificar_cambio_de_dia(datos)
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    url = "https://sorteosrd.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"⚠️ No se pudo conectar a la fuente en este intento: {e}")
        return False

    soup = BeautifulSoup(html, "html.parser")
    datos = cargar_datos()
    sorteos = datos.get("sorteos_hoy", [])
    hubo_cambios = False

    cards = soup.find_all("div", class_=re.compile(r"tarjeta-loteria|card", re.I))

    for s in sorteos:
        # 1. CANDADO DE RELOJ: Si aún no es la hora de este sorteo, no se toca
        if not hora_oficial_ha_pasado(s.get("hora", "")):
            continue

        for card in cards:
            texto = card.get_text(separator=" ", strip=True)

            if emparejar_sorteo(s["nombre"], s.get("hora", ""), texto):
                # 2. CANDADO DE FECHA: Si la tarjeta externa no tiene la fecha de hoy, se descarta
                if not validar_fecha_tarjeta(texto):
                    continue

                nums = re.findall(r"\b(\d{2})\b", texto)
                if len(nums) >= 3:
                    p1, p2, p3 = int(nums[0]), int(nums[1]), int(nums[2])
                    if s["estado"] != "finalizado" or s.get("premios") != [p1, p2, p3]:
                        print(f"🎉 ¡NUEVO RESULTADO OFICIAL DETECTADO: {s['nombre']} -> [{p1:02d} - {p2:02d} - {p3:02d}]!")
                        s["estado"] = "finalizado"
                        s["premios"] = [p1, p2, p3]
                        actualizar_historial_local(s.get("id", ""), [p1, p2, p3])
                        hubo_cambios = True
                        break

    if hubo_cambios:
        datos["actualizado_a_las"] = datetime.now().strftime("%I:%M %p")
        guardar_datos(datos)
        print("⚡ Efecto Cascada recalculado y sincronizado automáticamente.")
    else:
        print("✓ Sin sorteos nuevos por ahora. Pizarra y horarios 100% protegidos.")
        
    return hubo_cambios

if __name__ == "__main__":
    print("==========================================================")
    print("   ROBOT RASTREADOR AUTOMÁTICO EN VIVO - LOTOPRO RD")
    print("==========================================================")
    
    if "--bucle" in sys.argv:
        print("🚀 Modo Bucle Automático Activado (Rastrea cada 3 minutos)...")
        print("Presiona Ctrl + C para detener en cualquier momento.\n")
        while True:
            try:
                escanear_sorteos_en_vivo()
                time.sleep(180)
            except KeyboardInterrupt:
                print("\n🛑 Robot detenido por el usuario.")
                break
    else:
        escanear_sorteos_en_vivo()
        print("\nPara dejarlo funcionando solo todo el día en segundo plano:")
        print("  python robot_rastreador.py --bucle")
