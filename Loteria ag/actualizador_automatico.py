import os
import sys
import time
import ssl
import json
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime
from motor_jugada_maestra import calcular_jugada_maestra

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_JSON = os.path.join(DIR_ACTUAL, "sorteos_hoy.json")
ARCHIVO_JS = os.path.join(DIR_ACTUAL, "datos_en_vivo.js")
ARCHIVO_HIST = os.path.join(DIR_ACTUAL, "historial_loterias.json")
ARCHIVO_HIST_JS = os.path.join(DIR_ACTUAL, "datos_historial.js")

MAPA_LOTERIAS = {
    "anguilla 10am": "anguila_10am",
    "la primera": "la_primera_dia",
    "la suerte": "la_suerte_dia",
    "real": "quiniela_real",
    "anguilla 1pm": "anguila_1pm",
    "new jersey tarde": "new_jersey_dia",
    "florida tarde": "florida_dia",
    "lotedom": "lotedom",
    "nacional gana más": "gana_mas",
    "gana más": "gana_mas",
    "new york tarde": "ny_tarde",
    "la suerte 6pm": "la_suerte_tarde",
    "anguilla 6pm": "anguila_6pm",
    "loteka": "quiniela_loteka",
    "la primera noche": "primera_noche",
    "leidsa": "quiniela_leidsa",
    "nacional noche": "loteria_nacional",
    "real noche": "real_noche",
    "anguilla 9pm": "anguila_9pm",
    "florida noche": "florida_noche",
    "new york noche": "ny_noche"
}

def hora_ha_pasado(hora_str):
    try:
        ahora = datetime.now()
        t = datetime.strptime(hora_str.strip(), "%I:%M %p")
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
        nom_clean = nombre_sorteo.lower()
        for h in wb.sheetnames:
            h_clean = h.lower()
            if h_clean in nom_clean or nom_clean in h_clean:
                hoja_match = h
                break
        if not hoja_match and wb.sheetnames:
            pref = sid.split('_')[0]
            for h in wb.sheetnames:
                if pref in h.lower():
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
    print(f"[{datetime.now().strftime('%I:%M:%S %p')}] 📡 Consultando resultados oficiales en vivo...")
    
    # 1. Cargar datos locales
    with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
        datos = json.load(f)

    # 2. Verificar cambio de día
    hoy_iso = datetime.now().strftime("%Y-%m-%d")
    hoy_dmy = datetime.now().strftime("%d/%m/%Y")
    
    if datos.get("fecha_hoy") != hoy_iso:
        print(f"🌅 ¡Nuevo día detectado ({hoy_iso})! Archivando sorteos de ayer...")
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
            
        datos["fecha_ayer"] = datos.get("fecha_hoy", "")
        datos["fecha_hoy"] = hoy_iso
        
        for s in datos.get("sorteos_hoy", []):
            s["estado"] = "proximo"
            s["premios"] = None
            if "alerta_cascada" in s:
                del s["alerta_cascada"]

        with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
            
        nueva_pareja = calcular_jugada_maestra()
        datos["jugada_maestra_fija"]["pareja_oficial"] = nueva_pareja
        print(f"🎯 Nueva Pareja Maestra Calculada: [ {nueva_pareja[0]} ] × [ {nueva_pareja[1]} ]")

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
    
    with open(ARCHIVO_HIST, "r", encoding="utf-8") as f:
        hist = json.load(f)

    hubo_cambios = False
    
    # 4. Procesar tarjetas de resultados
    for card in soup.find_all("div", class_="result-card"):
        name_el = card.find(class_="lottery-name")
        if not name_el:
            continue
        nom_web = name_el.get_text(strip=True).lower()
        
        # Encontrar ID correspondiente
        sid = None
        for k, v in MAPA_LOTERIAS.items():
            if k in nom_web:
                sid = v
                break
        if not sid:
            continue

        # Extraer bolos
        balls = card.find_all(class_="result-number")
        if len(balls) < 3:
            continue
        nums = [int(b.get_text(strip=True)) for b in balls[:3]]

        # Extraer fecha de la tarjeta
        date_el = card.find(class_="result-date")
        date_txt = date_el.get_text(strip=True).lower() if date_el else ""

        # Verificar si la tarjeta es de hoy
        dia_num = str(datetime.now().day)
        if dia_num not in date_txt:
            continue # Tarjeta vieja, descartar

        # Buscar sorteo en sorteos_hoy
        for s in datos.get("sorteos_hoy", []):
            if s.get("id") == sid:
                # Candado de reloj
                if not hora_ha_pasado(s.get("hora", "")):
                    continue

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
        datos["actualizado_a_las"] = datetime.now().strftime("%I:%M %p")
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
    print("   LOTOPRO RD — ACTUALIZADOR AUTOMÁTICO DE RESULTADOS")
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
