import os
import sys
import time
import ssl
import json
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from motor_jugada_maestra import calcular_jugada_maestra

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Zona Horaria Fija de República Dominicana (UTC-4) sin importar dónde corra el servidor (Londres, EE.UU., etc.)
TZ_RD = timezone(timedelta(hours=-4))

def ahora_rd():
    return datetime.now(TZ_RD)

DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_JSON = os.path.join(DIR_ACTUAL, "sorteos_hoy.json")
ARCHIVO_JS = os.path.join(DIR_ACTUAL, "datos_en_vivo.js")
ARCHIVO_HIST = os.path.join(DIR_ACTUAL, "historial_loterias.json")
ARCHIVO_HIST_JS = os.path.join(DIR_ACTUAL, "datos_historial.js")

# Mapeo exhaustivo de nombres web a IDs internos.
# Las búsquedas se ordenan de mayor longitud a menor para evitar colisiones (ej: 'la suerte 6pm' antes de 'la suerte').
MAPA_LOTERIAS = {
    # Anguila
    "anguilla 10am": "anguila_10am",
    "anguila 10am": "anguila_10am",
    "anguilla 10:00": "anguila_10am",
    "anguilla 1pm": "anguila_1pm",
    "anguila 1pm": "anguila_1pm",
    "anguilla 1:00": "anguila_1pm",
    "anguilla 6pm": "anguila_6pm",
    "anguila 6pm": "anguila_6pm",
    "anguilla 6:00": "anguila_6pm",
    "anguilla 9pm": "anguila_9pm",
    "anguila 9pm": "anguila_9pm",
    "anguilla 9:00": "anguila_9pm",
    # Primera
    "la primera noche": "primera_noche",
    "primera noche": "primera_noche",
    "la primera 8pm": "primera_noche",
    "la primera 8:00": "primera_noche",
    "la primera dia": "la_primera_dia",
    "la primera 12pm": "la_primera_dia",
    "la primera 12:00": "la_primera_dia",
    "la primera": "la_primera_dia",
    # Suerte
    "la suerte 6pm": "la_suerte_tarde",
    "la suerte 6:00": "la_suerte_tarde",
    "suerte 6pm": "la_suerte_tarde",
    "la suerte tarde": "la_suerte_tarde",
    "la suerte 12:30": "la_suerte_dia",
    "la suerte 12pm": "la_suerte_dia",
    "la suerte dia": "la_suerte_dia",
    "la suerte": "la_suerte_dia",
    # Real
    "real noche": "real_noche",
    "real 9pm": "real_noche",
    "real 9:00": "real_noche",
    "quiniela real": "quiniela_real",
    "real 1pm": "quiniela_real",
    "real 1:00": "quiniela_real",
    "real": "quiniela_real",
    # New Jersey
    "new jersey tarde": "new_jersey_dia",
    "new jersey 1pm": "new_jersey_dia",
    "new jersey 1:00": "new_jersey_dia",
    "new jersey": "new_jersey_dia",
    # Florida
    "florida noche": "florida_noche",
    "florida 10pm": "florida_noche",
    "florida 10:00": "florida_noche",
    "florida tarde": "florida_dia",
    "florida 1:30": "florida_dia",
    "florida 1pm": "florida_dia",
    "florida": "florida_dia",
    # Lotedom
    "lotedom": "lotedom",
    # Nacional / Gana Más
    "nacional gana más": "gana_mas",
    "nacional gana mas": "gana_mas",
    "gana más": "gana_mas",
    "gana mas": "gana_mas",
    "gana mas 2:30": "gana_mas",
    "nacional noche": "loteria_nacional",
    "loteria nacional": "loteria_nacional",
    "nacional 9pm": "loteria_nacional",
    # New York
    "new york noche": "ny_noche",
    "new york 10:30": "ny_noche",
    "new york tarde": "ny_tarde",
    "new york 2:30": "ny_tarde",
    # Loteka
    "quiniela loteka": "quiniela_loteka",
    "loteka 7:55": "quiniela_loteka",
    "loteka": "quiniela_loteka",
    # Leidsa
    "quiniela leidsa": "quiniela_leidsa",
    "leidsa 8:55": "quiniela_leidsa",
    "leidsa": "quiniela_leidsa"
}

# URLs individuales por si alguna lotería requiere consulta directa de respaldo
URLS_RESPALDO = {
    "anguila_10am": ("https://enloteria.com/resultados-anguilla-10am", "Anguilla 10AM"),
    "la_primera_dia": ("https://enloteria.com/resultados-la-primera", "La Primera"),
    "la_suerte_dia": ("https://enloteria.com/resultados-la-suerte", "La Suerte"),
    "quiniela_real": ("https://enloteria.com/resultados-real", "Real"),
    "anguila_1pm": ("https://enloteria.com/resultados-anguilla-1pm", "Anguilla 1PM"),
    "new_jersey_dia": ("https://enloteria.com/resultados-new-jersey-tarde", "New Jersey Tarde"),
    "florida_dia": ("https://enloteria.com/resultados-florida-tarde", "Florida Tarde"),
    "lotedom": ("https://enloteria.com/resultados-lotedom", "LoteDom"),
    "gana_mas": ("https://enloteria.com/resultados-gana-mas", "Nacional Gana"),
    "ny_tarde": ("https://enloteria.com/resultados-new-york-tarde", "New York Tarde"),
    "la_suerte_tarde": ("https://enloteria.com/resultados-la-suerte-6pm", "La Suerte 6PM"),
    "anguila_6pm": ("https://enloteria.com/resultados-anguilla-6pm", "Anguilla 6PM"),
    "quiniela_loteka": ("https://enloteria.com/resultados-loteka", "Loteka"),
    "primera_noche": ("https://enloteria.com/resultados-la-primera-noche", "La Primera Noche"),
    "quiniela_leidsa": ("https://enloteria.com/resultados-leidsa", "Leidsa"),
    "loteria_nacional": ("https://enloteria.com/resultados-nacional-noche", "Nacional Noche"),
    "real_noche": ("https://enloteria.com/resultados-real-noche", "Real Noche"),
    "anguila_9pm": ("https://enloteria.com/resultados-anguilla-9pm", "Anguilla 9PM"),
    "florida_noche": ("https://enloteria.com/resultados-florida-noche", "Florida Noche"),
    "ny_noche": ("https://enloteria.com/resultados-new-york-noche", "New York Noche")
}

def hora_ha_pasado(hora_str):
    try:
        ahora = ahora_rd()
        t = datetime.strptime(hora_str.strip(), "%I:%M %p")
        # El sorteo ya debió salir si la hora actual en RD es mayor o igual
        return (ahora.hour * 60 + ahora.minute) >= (t.hour * 60 + t.minute)
    except Exception:
        return True

def sincronizar_excel_recientes(sid, nombre_sorteo, fecha_dmy, premios):
    archivo_excel = os.path.join(DIR_ACTUAL, "Recientes.xlsx")
    if not os.path.exists(archivo_excel):
        return
    try:
        import openpyxl
        wb = openpyxl.load_workbook(archivo_excel)
        hoja_match = None
        nom_clean = nombre_sorteo.lower().replace(":", ".").replace(" ", "")
        for h in wb.sheetnames:
            h_clean = h.lower().replace(":", ".").replace(" ", "")
            if h_clean == nom_clean:
                hoja_match = h
                break
        if not hoja_match:
            for h in wb.sheetnames:
                h_clean = h.lower().replace(":", ".").replace(" ", "")
                if h_clean in nom_clean or nom_clean in h_clean:
                    hoja_match = h
                    break
        if hoja_match:
            ws = wb[hoja_match]
            if ws.max_row >= 2 and str(ws.cell(row=2, column=1).value).strip() == fecha_dmy:
                ws.cell(row=2, column=2, value=premios[0])
                ws.cell(row=2, column=3, value=premios[1])
                ws.cell(row=2, column=4, value=premios[2])
            else:
                ws.insert_rows(2)
                ws.cell(row=2, column=1, value=fecha_dmy)
                ws.cell(row=2, column=2, value=premios[0])
                ws.cell(row=2, column=3, value=premios[1])
                ws.cell(row=2, column=4, value=premios[2])
            wb.save(archivo_excel)
            print(f"📊 Recientes.xlsx sincronizado: {hoja_match} -> {premios}")
    except Exception as e:
        print(f"Nota sincronizando Recientes.xlsx: {e}")

def actualizar_todo():
    hora_actual_str = ahora_rd().strftime('%I:%M:%S %p')
    print(f"[{hora_actual_str} RD] 📡 Consultando resultados oficiales en vivo...")
    
    # 1. Cargar datos locales
    with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
        datos = json.load(f)

    # 2. Verificar cambio de día con HORA DE REPÚBLICA DOMINICANA (UTC-4)
    ahora = ahora_rd()
    hoy_iso = ahora.strftime("%Y-%m-%d")
    hoy_dmy = ahora.strftime("%d/%m/%Y")
    hubo_cambios = False
    
    if datos.get("fecha_hoy") != hoy_iso:
        print(f"🌅 ¡Nuevo día detectado en RD ({hoy_iso})! Archivando sorteos de ayer...")
        sorteos_ayer = []
        for s in datos.get("sorteos_hoy", []):
            if s.get("premios"):
                sorteos_ayer.append({
                    "nombre": s["nombre"],
                    "hora": s["hora"],
                    "premios": s["premios"]
                })
        if len(sorteos_ayer) >= 15:
            datos["sorteos_ayer"] = sorteos_ayer
            
        datos["fecha_ayer"] = datos.get("fecha_hoy", "")
        datos["fecha_hoy"] = hoy_iso
        
        for s in datos.get("sorteos_hoy", []):
            s["estado"] = "proximo"
            s["premios"] = None
            if "alerta_cascada" in s:
                del s["alerta_cascada"]

        nueva_pareja = calcular_jugada_maestra()
        datos["jugada_maestra_fija"]["pareja_oficial"] = nueva_pareja
        print(f"🎯 Nueva Pareja Maestra Oficial: [ {nueva_pareja[0]} ] × [ {nueva_pareja[1]} ]")
        hubo_cambios = True

    # 3. Descargar resultados de enloteria.com
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = "https://enloteria.com/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, context=ctx, timeout=12).read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"⚠️ Error conectando a la fuente: {e}")
        return False

    soup = BeautifulSoup(html, "html.parser")
    
    hist = {}
    if os.path.exists(ARCHIVO_HIST):
        with open(ARCHIVO_HIST, "r", encoding="utf-8") as f:
            hist = json.load(f)

    # Ordenar claves de búsqueda por longitud descendente para evitar colisiones
    claves_ordenadas = sorted(MAPA_LOTERIAS.keys(), key=len, reverse=True)

    # 4. Procesar tarjetas de resultados de la página principal
    dia_num = str(ahora.day)
    
    for card in soup.find_all("div", class_="result-card"):
        name_el = card.find(class_="lottery-name")
        if not name_el:
            continue
        nom_web = name_el.get_text(strip=True).lower()
        
        # Encontrar ID correspondiente sin colisiones
        sid = None
        for k in claves_ordenadas:
            if k in nom_web:
                sid = MAPA_LOTERIAS[k]
                break
        if not sid:
            continue

        # Extraer bolos
        balls = card.find_all(class_="result-number")
        nums = [int(b.get_text(strip=True)) for b in balls if b.get_text(strip=True).isdigit()]
        if len(nums) < 3:
            continue
        nums = nums[:3]

        # Extraer fecha de la tarjeta
        date_el = card.find(class_="result-date")
        date_txt = date_el.get_text(strip=True).lower() if date_el else ""

        # Verificar si la tarjeta es de hoy en RD
        if dia_num not in date_txt:
            continue

        # Buscar sorteo en sorteos_hoy
        for s in datos.get("sorteos_hoy", []):
            if s.get("id") == sid:
                if s["estado"] != "finalizado" or s.get("premios") != nums:
                    print(f"🎉 ¡NUEVO RESULTADO OFICIAL DETECTADO: {s['nombre']} -> {nums}!")
                    s["estado"] = "finalizado"
                    s["premios"] = nums
                    
                    # Actualizar historial
                    if sid not in hist:
                        hist[sid] = []
                    if hist[sid] and hist[sid][0].get("fecha") == hoy_dmy:
                        hist[sid][0]["premios"] = nums
                    else:
                        hist[sid].insert(0, {"fecha": hoy_dmy, "premios": nums})
                        
                    hubo_cambios = True
                    sincronizar_excel_recientes(sid, s.get("nombre", sid), hoy_dmy, nums)

    if hubo_cambios:
        datos["actualizado_a_las"] = ahora.strftime("%I:%M %p")
        with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        with open(ARCHIVO_JS, "w", encoding="utf-8") as f:
            f.write("window.DATOS_LOTOPRO = " + json.dumps(datos, indent=2, ensure_ascii=False) + ";\n")
        with open(ARCHIVO_HIST, "w", encoding="utf-8") as f:
            json.dump(hist, f, indent=2, ensure_ascii=False)
        with open(ARCHIVO_HIST_JS, "w", encoding="utf-8") as f:
            f.write("window.HISTORIAL_LOTERIAS = " + json.dumps(hist, ensure_ascii=False) + ";\n")
        print("✅ Base de datos e historiales sincronizados al 100%.")
    else:
        print("✓ Pizarra al día. Sin sorteos nuevos por el momento.")

    return hubo_cambios

if __name__ == "__main__":
    print("==========================================================")
    print("   LOTOPRO RD — ACTUALIZADOR AUTÓNOMO 24/7 (ZONA HORARIA RD)")
    print("==========================================================")
    if "--bucle" in sys.argv:
        print("🚀 Modo Autónomo Continuo Activo (Rastrea cada 3 minutos)...")
        print("Presiona Ctrl + C para detener.\n")
        while True:
            try:
                actualizar_todo()
                time.sleep(180)
            except KeyboardInterrupt:
                print("\n🛑 Proceso detenido por el usuario.")
                break
    else:
        actualizar_todo()
