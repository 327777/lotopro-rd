import os
import sys
import time
import ssl
import json
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from motor_jugada_maestra import calcular_jugada_maestra, calcular_radar_vaiven

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

MAPA_HOJAS_EXCEL = {
    "anguila_10am": "Anguila 10.00 AM",
    "la_primera_dia": "La Primera Día",
    "la_suerte_dia": "La Suerte Día",
    "quiniela_real": "Quiniela Real",
    "anguila_1pm": "Anguila 1.00 PM",
    "new_jersey_dia": "New Jersey Día",
    "florida_dia": "Florida Día",
    "lotedom": "LoteDom",
    "gana_mas": "Gana Más",
    "ny_tarde": "New York Tarde",
    "la_suerte_tarde": "La Suerte Tarde",
    "anguila_6pm": "Anguila 6.00 PM",
    "quiniela_loteka": "Quiniela Loteka",
    "primera_noche": "Primera Noche",
    "quiniela_leidsa": "Quiniela Leidsa",
    "loteria_nacional": "Lotería Nacional",
    "real_noche": "Lotería Real Noche",
    "anguila_9pm": "Anguila 9.00 PM",
    "florida_noche": "Florida Noche",
    "ny_noche": "New York Noche"
}

def sincronizar_excel_recientes(sid, nombre_sorteo, fecha_dmy, premios):
    archivo_excel = os.path.join(DIR_ACTUAL, "Recientes.xlsx")
    if not os.path.exists(archivo_excel):
        return
    try:
        import openpyxl
        wb = openpyxl.load_workbook(archivo_excel)
        hoja_match = MAPA_HOJAS_EXCEL.get(sid)
        if not hoja_match or hoja_match not in wb.sheetnames:
            nom_clean = nombre_sorteo.lower().replace(":", ".").replace(" ", "")
            for h in wb.sheetnames:
                h_clean = h.lower().replace(":", ".").replace(" ", "")
                if h_clean == nom_clean or h_clean in nom_clean or nom_clean in h_clean:
                    hoja_match = h
                    break
        if hoja_match and hoja_match in wb.sheetnames:
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

def verificar_impacto_ciclo_maduracion(datos, sid, nombre_sorteo, fecha_dmy, nums):
    """
    Opción A: Monitorea si la jugada fija en ciclo de maduración cumple su objetivo
    de romper en 1ra (Mayor) en las 3 Loterías Clave: Gana Más, New York Tarde o Loteka.
    """
    jm = datos.get("jugada_maestra_fija", {})
    ciclo = jm.get("ciclo_maduracion", {})
    if not ciclo.get("activo", True):
        return

    pareja = jm.get("pareja_oficial", ["09", "59"])
    try:
        pareja_ints = [int(p) for p in pareja if str(p).isdigit()]
    except Exception:
        pareja_ints = [9, 59]

    loterias_clave = ciclo.get("loterias_clave", ["gana_mas", "ny_tarde", "quiniela_loteka"])

    if sid in loterias_clave and len(nums) >= 1:
        p0 = int(nums[0])
        if p0 in pareja_ints:
            print(f"\n{'='*60}")
            print(f"🏆🏆 ¡¡OBJETIVO CUMPLIDO: RUPTURA EN 1RA EN LOTERÍA MADURA CLAVE!! 🏆🏆")
            print(f"   Lotería: {nombre_sorteo}")
            print(f"   Premio Mayor Ganador: {p0:02d}")
            print(f"   Fecha: {fecha_dmy}")
            print(f"{'='*60}\n")
            ciclo["rompio_en_1ra"] = True
            ciclo["estado"] = f"¡OBJETIVO CUMPLIDO! Rompió {p0:02d} en 1ra en {nombre_sorteo}"
            ciclo["detalle_ruptura"] = {
                "loteria_id": sid,
                "loteria_nombre": nombre_sorteo,
                "fecha": fecha_dmy,
                "numero_ganador": f"{p0:02d}"
            }

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
        # Archivar siempre que haya al menos 1 sorteo finalizado (inmune a feriados y días con pocos sorteos)
        if len(sorteos_ayer) > 0:
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

        # Opción A: Bloquear Jugada Maestra en ciclo de maduración (3 a 5 días)
        jm = datos.get("jugada_maestra_fija", {})
        if "ciclo_maduracion" not in jm:
            jm["ciclo_maduracion"] = {
                "activo": True,
                "bloqueado": True,
                "fecha_inicio": "2026-10-07",
                "dias_activo": 6,
                "max_dias_ciclo": 5,
                "loterias_clave": ["gana_mas", "ny_tarde", "quiniela_loteka"],
                "loterias_clave_nombres": [
                    "Gana Más (2:30 PM)",
                    "New York Tarde (2:30 PM)",
                    "Quiniela Loteka (7:55 PM)"
                ],
                "objetivo": "Ruptura en 1ra Mayor en Lotería Madura Clave",
                "rompio_en_1ra": False,
                "detalle_ruptura": None,
                "estado": "En Maduración Activa"
            }
        
        ciclo = jm["ciclo_maduracion"]
        modo = jm.get("modo_ciclo", "maduracion_fija")

        # Calcular días transcurridos reales desde el inicio del ciclo
        fecha_inicio_str = ciclo.get("fecha_inicio", "2026-10-07")
        try:
            d_ini = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            d_hoy = ahora.date()
            dias_transcurridos = max(1, (d_hoy - d_ini).days + 1)
        except Exception:
            dias_transcurridos = ciclo.get("dias_activo", 1) + 1

        ciclo["dias_activo"] = dias_transcurridos

        if modo == "maduracion_fija" and ciclo.get("bloqueado", True):
            if ciclo.get("rompio_en_1ra", False):
                print(f"🎯 El ciclo previo CUMPLIÓ su objetivo de 1ra en {ciclo.get('detalle_ruptura', {}).get('loteria_nombre', 'lotería clave')}.")
                print(f"🔄 Calculando nuevo ciclo de maduración cuantitativo...")
                nueva_pareja = calcular_jugada_maestra()
                jm["pareja_oficial"] = nueva_pareja
                ciclo["fecha_inicio"] = hoy_iso
                ciclo["dias_activo"] = 1
                ciclo["rompio_en_1ra"] = False
                ciclo["detalle_ruptura"] = None
                ciclo["estado"] = f"En Maduración Activa (Día 1 de {ciclo.get('max_dias_ciclo', 5)})"
                print(f"🎯 Nueva Pareja Maestra Oficial: [ {nueva_pareja[0]} ] × [ {nueva_pareja[1]} ]")
            else:
                p1, p2 = jm.get("pareja_oficial", ["09", "59"])
                max_dias = ciclo.get("max_dias_ciclo", 5)
                ciclo["estado"] = f"En Maduración Activa (Día {dias_transcurridos} de {max_dias})"
                print(f"🔒 CICLO DE MADURACIÓN FIJO (Día {dias_transcurridos} de {max_dias}):")
                print(f"   Pareja Maestra [ {p1} ] × [ {p2} ] SE MANTIENE BLOQUEADA.")
                print(f"   Objetivo: Ruptura en 1ra en Gana Más, NY Tarde o Loteka.")
        else:
            nueva_pareja = calcular_jugada_maestra()
            jm["pareja_oficial"] = nueva_pareja
            print(f"🎯 Nueva Pareja Maestra Diaria: [ {nueva_pareja[0]} ] × [ {nueva_pareja[1]} ]")

        hubo_cambios = True

    hist = {}
    if os.path.exists(ARCHIVO_HIST):
        with open(ARCHIVO_HIST, "r", encoding="utf-8") as f:
            hist = json.load(f)

    # 2.5 Orden Oficial Cronológico Estricto (10:00 AM -> 10:30 PM)
    ORDEN_OFICIAL_IDS = [
        "anguila_10am",      # 10:00 AM
        "la_primera_dia",    # 12:00 PM
        "lotedom",           # 12:00 PM (Ubicado en su orden exacto del mediodía)
        "la_suerte_dia",     # 12:30 PM
        "quiniela_real",     # 1:00 PM
        "anguila_1pm",       # 1:00 PM
        "new_jersey_dia",    # 1:00 PM
        "florida_dia",       # 1:30 PM
        "gana_mas",          # 2:30 PM
        "ny_tarde",          # 2:30 PM
        "la_suerte_tarde",   # 6:00 PM
        "anguila_6pm",       # 6:00 PM
        "quiniela_loteka",   # 7:55 PM
        "primera_noche",     # 8:00 PM
        "quiniela_leidsa",   # 8:55 PM
        "loteria_nacional",  # 9:00 PM
        "real_noche",        # 9:00 PM
        "anguila_9pm",       # 9:00 PM
        "florida_noche",     # 10:00 PM
        "ny_noche"           # 10:30 PM
    ]
    ORDEN_OFICIAL_NOMBRES = [
        "Anguila 10:00 AM",
        "La Primera 12:00 PM",
        "LoteDom 12:00 PM",
        "La Suerte 12:30 PM",
        "Quiniela Real 1:00 PM",
        "Anguila 1:00 PM",
        "New Jersey 1:00 PM",
        "Florida 1:30 PM",
        "Gana Más 2:30 PM",
        "New York 2:30 PM",
        "La Suerte 6:00 PM",
        "Anguila 6:00 PM",
        "Quiniela Loteka 7:55 PM",
        "La Primera 8:00 PM",
        "Quiniela Leidsa 8:55 PM",
        "Lotería Nacional 9:00 PM",
        "Real 9:00 PM",
        "Anguila 9:00 PM",
        "Florida 10:00 PM",
        "New York 10:30 PM"
    ]

    if "sorteos_hoy" in datos:
        orden_actual_hoy = [s.get("id") for s in datos["sorteos_hoy"]]
        hoy_ordenado = sorted(
            datos["sorteos_hoy"],
            key=lambda s: ORDEN_OFICIAL_IDS.index(s.get("id")) if s.get("id") in ORDEN_OFICIAL_IDS else 999
        )
        if [s.get("id") for s in hoy_ordenado] != orden_actual_hoy:
            datos["sorteos_hoy"] = hoy_ordenado
            hubo_cambios = True

    if "sorteos_ayer" in datos:
        orden_actual_ayer = [s.get("nombre") for s in datos["sorteos_ayer"]]
        ayer_ordenado = sorted(
            datos["sorteos_ayer"],
            key=lambda s: ORDEN_OFICIAL_NOMBRES.index(s.get("nombre")) if s.get("nombre") in ORDEN_OFICIAL_NOMBRES else 999
        )
        if [s.get("nombre") for s in ayer_ordenado] != orden_actual_ayer:
            datos["sorteos_ayer"] = ayer_ordenado
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

    # Ordenar claves de búsqueda por longitud descendente para evitar colisiones
    claves_ordenadas = sorted(MAPA_LOTERIAS.keys(), key=len, reverse=True)

    # 4. Procesar tarjetas de resultados de la página principal (Tanto HOY como AYER para recuperación automática)
    import re
    sorteos_vistos_hoy = set()
    sorteos_vistos_ayer = set()
    
    ayer_dt = ahora - timedelta(days=1)
    ayer_dmy = ayer_dt.strftime("%d/%m/%Y")
    
    for card in soup.find_all("div", class_="result-card"):
        name_el = card.find(class_="lottery-name")
        date_el = card.find(class_="result-date")
        if not name_el or not date_el:
            continue
        nom_web = name_el.get_text(strip=True).lower()
        date_txt = date_el.get_text(strip=True).lower()
        
        m_dia = re.search(r"(\d{1,2})", date_txt)
        if not m_dia:
            continue
        dia_card = int(m_dia.group(1))
        
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

        # CASO 1: Sorteo de HOY
        if dia_card == ahora.day and sid not in sorteos_vistos_hoy:
            sorteos_vistos_hoy.add(sid)
            for s in datos.get("sorteos_hoy", []):
                if s.get("id") == sid and hora_ha_pasado(s.get("hora", "")):
                    if s["estado"] != "finalizado" or s.get("premios") != nums:
                        print(f"🎉 ¡NUEVO RESULTADO OFICIAL DETECTADO: {s['nombre']} -> {nums}!")
                        s["estado"] = "finalizado"
                        s["premios"] = nums
                        
                        if sid not in hist:
                            hist[sid] = []
                        if hist[sid] and hist[sid][0].get("fecha") == hoy_dmy:
                            hist[sid][0]["premios"] = nums
                        else:
                            hist[sid].insert(0, {"fecha": hoy_dmy, "premios": nums})
                            
                        hubo_cambios = True
                        sincronizar_excel_recientes(sid, s.get("nombre", sid), hoy_dmy, nums)
                        verificar_impacto_ciclo_maduracion(datos, sid, s.get("nombre", sid), hoy_dmy, nums)

        # CASO 2: RECUPERACIÓN INTELIGENTE DE AYER (Para sorteos nocturnos como NY Noche o Florida Noche)
        elif dia_card == ayer_dt.day and sid not in sorteos_vistos_ayer:
            sorteos_vistos_ayer.add(sid)
            
            necesita_recuperacion = False
            
            # Chequear si está en sorteos_ayer
            encontrado_en_ayer = False
            for s_ayer in datos.get("sorteos_ayer", []):
                if sid in s_ayer.get("nombre", "").lower() or s_ayer.get("premios") == nums:
                    encontrado_en_ayer = True
                    break
            if not encontrado_en_ayer:
                necesita_recuperacion = True
                
            # Chequear si está en historial
            if sid not in hist or not any(h.get("fecha") == ayer_dmy for h in hist.get(sid, [])):
                necesita_recuperacion = True

            if necesita_recuperacion:
                print(f"🌙 ¡RECUPERACIÓN NOCTURNA AUTOMÁTICA DE AYER: {sid} -> {nums}!")
                if sid not in hist:
                    hist[sid] = []
                hist_fechas = [h.get("fecha") for h in hist[sid]]
                if ayer_dmy not in hist_fechas:
                    hist[sid].append({"fecha": ayer_dmy, "premios": nums})
                    def k_date(x):
                        p = x.get("fecha", "").split("/")
                        return f"{p[2]}{p[1]}{p[0]}" if len(p) == 3 else "00000000"
                    hist[sid].sort(key=k_date, reverse=True)
                
                nombre_oficial = None
                hora_oficial = None
                for sh in datos.get("sorteos_hoy", []):
                    if sh.get("id") == sid:
                        nombre_oficial = sh.get("nombre")
                        hora_oficial = sh.get("hora")
                        break
                
                if nombre_oficial:
                    ayer_lista = datos.setdefault("sorteos_ayer", [])
                    actualizado_en_lista = False
                    for sa in ayer_lista:
                        if sa.get("nombre") == nombre_oficial:
                            sa["premios"] = nums
                            actualizado_en_lista = True
                            break
                    if not actualizado_en_lista:
                        ayer_lista.append({
                            "nombre": nombre_oficial,
                            "hora": hora_oficial,
                            "premios": nums
                        })
                
                sincronizar_excel_recientes(sid, nombre_oficial or sid, ayer_dmy, nums)
                hubo_cambios = True

    # 4.5 Respaldo Individual: Consultar URL individual para sorteos cuya hora ya pasó y no salieron en portada
    for s in datos.get("sorteos_hoy", []):
        sid = s.get("id")
        if s.get("estado") != "finalizado" and hora_ha_pasado(s.get("hora", "")) and sid in URLS_RESPALDO:
            try:
                url_resp, nom_resp = URLS_RESPALDO[sid]
                req_resp = urllib.request.Request(url_resp, headers=headers)
                html_resp = urllib.request.urlopen(req_resp, context=ctx, timeout=8).read().decode("utf-8", errors="ignore")
                soup_resp = BeautifulSoup(html_resp, "html.parser")
                cards_resp = soup_resp.find_all("div", class_="result-card")
                for card_resp in cards_resp:
                    date_el = card_resp.find(class_="result-date")
                    date_txt = date_el.get_text(strip=True).lower() if date_el else ""
                    m_d = re.search(r"(\d{1,2})", date_txt)
                    if m_d and int(m_d.group(1)) == ahora.day:
                        balls = card_resp.find_all(class_="result-number")
                        nums = [int(b.get_text(strip=True)) for b in balls if b.get_text(strip=True).isdigit()]
                        if len(nums) >= 3:
                            nums = nums[:3]
                            print(f"🎉 ¡RESPALDO EXITOSO: {s['nombre']} -> {nums}!")
                            s["estado"] = "finalizado"
                            s["premios"] = nums
                            if sid not in hist:
                                hist[sid] = []
                            if hist[sid] and hist[sid][0].get("fecha") == hoy_dmy:
                                hist[sid][0]["premios"] = nums
                            else:
                                hist[sid].insert(0, {"fecha": hoy_dmy, "premios": nums})
                            hubo_cambios = True
                            sincronizar_excel_recientes(sid, s.get("nombre", sid), hoy_dmy, nums)
                            verificar_impacto_ciclo_maduracion(datos, sid, s.get("nombre", sid), hoy_dmy, nums)
                            break
            except Exception as e_resp:
                pass

    # 5. Seguridad: Solo sorteos que NO hayan finalizado y cuya hora aún no haya llegado se aseguran en "proximo"
    # UN SORTEO QUE YA FINALIZÓ HOY NUNCA SE BORRA NI SE REGRESA A "PROXIMO" (INMUNE A FERIADOS Y HORARIOS ESPECIALES)
    for s in datos.get("sorteos_hoy", []):
        if s.get("estado") != "finalizado":
            if not hora_ha_pasado(s.get("hora", "")):
                if s.get("estado") != "proximo" or s.get("premios") is not None:
                    s["estado"] = "proximo"
                    s["premios"] = None
                    hubo_cambios = True

    # 4.8 Actualizar Radar de Vaivén Armónico & Frecuencia (Top 6 Loterías Estratégicas)
    try:
        pareja_act = datos.get("jugada_maestra_fija", {}).get("pareja_oficial", ["09", "59"])
        radar_calc = calcular_radar_vaiven(datos.get("sorteos_hoy", []), pareja_act)
        datos["radar_vaiven_top4"] = radar_calc
        datos["radar_vaiven_top6"] = radar_calc
    except Exception as e:
        print(f"Aviso radar vaivén: {e}")

    if hubo_cambios or "radar_vaiven_top4" not in datos:
        datos["actualizado_a_las"] = ahora.strftime("%I:%M %p")
        with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        with open(ARCHIVO_JS, "w", encoding="utf-8") as f:
            f.write("window.DATOS_LOTOPRO = " + json.dumps(datos, indent=2, ensure_ascii=False) + ";\n")
        with open(ARCHIVO_HIST, "w", encoding="utf-8") as f:
            json.dump(hist, f, indent=2, ensure_ascii=False)
        with open(ARCHIVO_HIST_JS, "w", encoding="utf-8") as f:
            f.write("window.HISTORIAL_LOTERIAS = " + json.dumps(hist, ensure_ascii=False) + ";\n")
        print("✅ Base de datos, historiales y Radar de Vaivén sincronizados al 100%.")
    else:
        # Guardar también el radar en caso de que esté corriendo sin cambios de resultados
        with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        with open(ARCHIVO_JS, "w", encoding="utf-8") as f:
            f.write("window.DATOS_LOTOPRO = " + json.dumps(datos, indent=2, ensure_ascii=False) + ";\n")
        print("✓ Pizarra al día. Radar de Vaivén actualizado.")

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
