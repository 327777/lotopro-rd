from datetime import datetime, timedelta
import sys
import pandas as pd

# Forzar codificación UTF-8 en la consola
sys.stdout.reconfigure(encoding="utf-8")

VERDE = "\033[92m"
CIAN = "\033[96m"
ROJO = "\033[91m"
RESET = "\033[0m"

print(f"{CIAN}--- ACTIVANDO MOTOR DE PRECISIÓN QUIRÚRGICA (FECHA REAL) ---{RESET}")

nombre_copia = "Recientes.xlsx"

try:
    hojas_dict = pd.read_excel(
        nombre_copia, sheet_name=None, dtype=str, engine="openpyxl"
    )
    print(f"{VERDE}Matriz leída con éxito.{RESET}")
except Exception as e:
    print(f"{ROJO}Error al abrir el archivo de Excel: {e}{RESET}")
    exit()

df_list = []
for nombre_hoja, df_hoja in hojas_dict.items():
    if df_hoja.empty:
        continue
    df_hoja.columns = df_hoja.columns.str.strip().str.upper()

    if len(df_hoja.columns) > 0:
        col_fecha = df_hoja.columns[0]
        df_temp = pd.DataFrame()
        # Limpiar la fecha quitando la hora si viene como '2026-09-02 00:00:00'
        df_temp["FECHA_RAW"] = (
            df_hoja[col_fecha]
            .astype(str)
            .str.strip()
            .str.split(" ")
            .str[0]
        )
        df_temp["LOTERIA"] = str(nombre_hoja).strip()

        for col in ["1ER", "2DO", "3ER", "3RO"]:
            if col in df_hoja.columns:
                nombre_pos = "3RO" if col in ["3ER", "3RO"] else col
                df_temp[nombre_pos] = df_hoja[col]

        # Parsear fechas limpias
        df_temp["FECHA_PARSED"] = pd.to_datetime(
            df_temp["FECHA_RAW"], errors="coerce", dayfirst=True
        )

        df_temp = df_temp.dropna(subset=["FECHA_PARSED"])
        if not df_temp.empty:
            df_list.append(df_temp)

if not df_list:
    print(f"{ROJO}Error: No se encontraron fechas válidas.{RESET}")
    exit()

df_global = pd.concat(df_list, ignore_index=True)

# MÁXIMO GLOBAL REAL DETECTADO EN EL EXCEL (AHORA SÍ CAPTURA EL 02/09)
f_24h_exacta = df_global["FECHA_PARSED"].max()
fecha_ref = f_24h_exacta + timedelta(days=1)
f_3d_inicio = fecha_ref - timedelta(days=3)

print(
    f"{VERDE}>>> ÚLTIMO DÍA REAL DETECTADO EN EL EXCEL:"
    f" {f_24h_exacta.strftime('%d/%m/%Y')} <<<{RESET}"
)

df = df_global[df_global["FECHA_PARSED"] >= f_3d_inicio].sort_values(
    by="FECHA_PARSED"
)


def obtener_detalles_concordancia(df_filtrado):
    registros = []
    cols_premios = ["1ER", "2DO", "3RO"]
    for _, fila in df_filtrado.iterrows():
        fecha_dt = pd.to_datetime(fila["FECHA_PARSED"])
        fecha_str = fecha_dt.strftime("%d/%m/%Y")
        loteria_str = str(fila["LOTERIA"])
        for col_p in cols_premios:
            if col_p in df_filtrado.columns and pd.notnull(fila[col_p]):
                val = fila[col_p]
                try:
                    num = int(float(val))
                    if 0 <= num <= 99:
                        registros.append({
                            "NUMERO": f"{num:02d}",
                            "FECHA": fecha_str,
                            "LOTERIA": loteria_str,
                            "POSICION": (
                                "1RO"
                                if col_p == "1ER"
                                else ("2DO" if col_p == "2DO" else "3RO")
                            ),
                        })
                except:
                    continue
    return pd.DataFrame(registros)


df_24h = df_global[df_global["FECHA_PARSED"] == f_24h_exacta]
df_3d = df[
    (df["FECHA_PARSED"] >= f_3d_inicio) & (df["FECHA_PARSED"] <= f_24h_exacta)
]

df_det_24h = obtener_detalles_concordancia(df_24h)
df_det_3d = obtener_detalles_concordancia(df_3d)


def calcular_precision_quirurgica(df_base, f_inicio, f_fin, fecha_actual):
    cols_premios = ["1ER", "2DO", "3RO"]
    registros = []

    for _, fila in df_base.iterrows():
        fecha_dt = fila["FECHA_PARSED"]
        loteria = fila["LOTERIA"]
        for pos in cols_premios:
            if pos in df_base.columns and pd.notnull(fila[pos]):
                try:
                    num = int(float(fila[pos]))
                    if 0 <= num <= 99:
                        registros.append({
                            "FECHA": fecha_dt,
                            "LOTERIA": loteria,
                            "POSICION": (
                                "1RO"
                                if pos == "1ER"
                                else ("2DO" if pos == "2DO" else "3RO")
                            ),
                            "NUMERO": f"{num:02d}",
                        })
                except:
                    continue

    df_plano = pd.DataFrame(registros)
    if df_plano.empty:
        return []

    df_reciente = df_plano[
        (df_plano["FECHA"] >= f_inicio) & (df_plano["FECHA"] <= f_fin)
    ]
    conteo_reciente = (
        df_reciente["NUMERO"].value_counts()
        if not df_reciente.empty
        else pd.Series(dtype=int)
    )

    precision_lista = []
    nums_unicos = df_plano["NUMERO"].unique()

    for num in nums_unicos:
        hist_grupo = df_plano[df_plano["NUMERO"] == num]
        total_historico = len(hist_grupo)
        reciente_count = conteo_reciente.get(num, 0)

        fechas = hist_grupo["FECHA"].drop_duplicates().sort_values().tolist()
        dias_promedio = 0
        if len(fechas) >= 2:
            difs = [
                (fechas[i + 1] - fechas[i]).days
                for i in range(len(fechas) - 1)
            ]
            dias_promedio = sum(difs) / len(difs)

        ultima_fecha_dt = fechas[-1] if fechas else fecha_actual
        dias_desde_ultima = (fecha_actual - ultima_fecha_dt).days

        pos_counts = hist_grupo["POSICION"].value_counts()
        pos_dominante = pos_counts.index[0] if not pos_counts.empty else "N/A"
        certeza_pos = (
            (pos_counts.iloc[0] / total_historico) * 100
            if not pos_counts.empty
            else 0
        )

        factor_maduracion = 0
        if dias_desde_ultima == 0:
            factor_maduracion = -100
        elif dias_promedio > 0:
            diferencia = abs(dias_desde_ultima - dias_promedio)
            if diferencia <= 0.8:
                factor_maduracion = 60 - (diferencia * 30)
            elif diferencia <= 1.5:
                factor_maduracion = 30 - (diferencia * 10)
            else:
                factor_maduracion = max(0, 10 - diferencia)

        ipm = (
            (reciente_count * 10)
            + (certeza_pos * 0.2)
            + factor_maduracion
            + (20 if dias_desde_ultima == 1 else 0)
        )

        precision_lista.append({
            "NUMERO": num,
            "IPM": round(ipm, 1),
            "POS_DOMINANTE": pos_dominante,
            "FIABILIDAD_POS": round(certeza_pos, 1),
            "CICLO_DIAS": round(dias_promedio, 1),
            "DIAS_ATRASO": dias_desde_ultima,
            "ULTIMA_FECHA": (
                ultima_fecha_dt.strftime("%d/%m/%Y") if fechas else "N/A"
            ),
        })

    return sorted(precision_lista, key=lambda x: x["IPM"], reverse=True)


resultados_quirurgicos = calcular_precision_quirurgica(
    df_global, f_3d_inicio, f_24h_exacta, fecha_ref
)


def generar_filas_html_24h(df_det):
    if df_det.empty:
        return (
            "<tr><td colspan='3' style='padding:12px; text-align:center;"
            " color:#64748b;'>Sin registros</td></tr>"
        )
    html = ""
    conteo_freq = df_det["NUMERO"].value_counts()
    for num, freq in conteo_freq.items():
        apariciones = df_det[df_det["NUMERO"] == num]
        detalles_str = ""
        for _, ap in apariciones.iterrows():
            detalles_str += (
                f"<span style='display:inline-block; background:#f8fafc;"
                f" border:1px solid #e2e8f0; padding:3px 7px; margin:2px;"
                f" border-radius:4px; font-size:11px; color:#334155;'><b>{ap['FECHA']}</b>"
                f" | <span style='color:#0369a1;"
                f" font-weight:600;'>{ap['LOTERIA']}</span> <span"
                f" style='color:#64748b;'>({ap['POSICION']})</span></span>"
            )
        html += f"""
        <tr class='fila-numero' data-busqueda='{num}'>
            <td style='padding: 8px 10px; border-bottom: 1px solid #f1f5f9;'><strong style='color:#0369a1; font-size:14px;'>{num}</strong></td>
            <td style='padding: 8px 10px; border-bottom: 1px solid #f1f5f9; text-align: center;'><span style='background:#e0f2fe; color:#0369a1; padding:2px 8px; border-radius:10px; font-weight:700; font-size:11px;'>{freq}v</span></td>
            <td style='padding: 8px 10px; border-bottom: 1px solid #f1f5f9;'>{detalles_str}</td>
        </tr>
        """
    return html


def generar_filas_html_3d(df_det):
    if df_det.empty:
        return (
            "<tr><td colspan='3' style='padding:12px; text-align:center;"
            " color:#64748b;'>Sin registros</td></tr>"
        )
    html = ""
    conteo_freq = df_det["NUMERO"].value_counts()
    for num, freq in conteo_freq.items():
        apariciones = df_det[df_det["NUMERO"] == num]
        detalles_str = ""
        for _, ap in apariciones.iterrows():
            partes_fecha = ap["FECHA"].split("/")
            fecha_corta = f"{partes_fecha[0]}/{partes_fecha[1]}"
            meta_tag = (
                f"{num} {ap['FECHA']} {fecha_corta} {ap['LOTERIA']}"
                f" {ap['POSICION']}"
            ).lower()
            detalles_str += (
                f"<span class='badge-aparicion' data-filtro='{meta_tag}'"
                f" style='display:inline-block; background:#f8fafc; border:1px"
                f" solid #e2e8f0; padding:3px 7px; margin:2px;"
                f" border-radius:4px; font-size:11px;"
                f" color:#334155;'><b>{ap['FECHA']}</b> | <span"
                f" style='color:#0369a1;"
                f" font-weight:600;'>{ap['LOTERIA']}</span> <span"
                f" style='color:#64748b;'>({ap['POSICION']})</span></span>"
            )
        html += f"""
        <tr class='fila-numero-3d' data-numero='{num}'>
            <td style='padding: 8px 10px; border-bottom: 1px solid #f1f5f9;'><strong style='color:#7e22ce; font-size:14px;'>{num}</strong></td>
            <td style='padding: 8px 10px; border-bottom: 1px solid #f1f5f9; text-align: center;'><span class='contador-freq' style='background:#f3e8ff; color:#7e22ce; padding:2px 8px; border-radius:10px; font-weight:700; font-size:11px;'>{freq}v</span></td>
            <td style='padding: 8px 10px; border-bottom: 1px solid #f1f5f9;'>{detalles_str}</td>
        </tr>
        """
    return html


def generar_filas_quirurgicas(lista_precision):
    if not lista_precision:
        return (
            "<tr><td colspan='3' style='padding:12px; text-align:center;"
            " color:#64748b;'>Sin datos</td></tr>"
        )
    html = ""
    for item in lista_precision:
        if item["IPM"] <= 0:
            continue
        meta_certeza = f"{item['NUMERO']} {item['POS_DOMINANTE']}".lower()
        html += f"""
        <tr class='fila-certeza' data-busqueda='{meta_certeza}'>
            <td style='padding: 8px 10px; border-bottom: 1px solid #f1f5f9;'><strong style='color:#4f46e5; font-size:14px;'>{item['NUMERO']}</strong></td>
            <td style='padding: 8px 10px; border-bottom: 1px solid #f1f5f9; text-align: center;'><span style='background:#e0e7ff; color:#3730a3; padding:2px 8px; border-radius:10px; font-weight:700; font-size:11px;'>{item['IPM']} ipm</span></td>
            <td style='padding: 8px 10px; border-bottom: 1px solid #f1f5f9;'>
                <span style='font-size:11px; color:#334155;'>
                Pos: <b>{item['POS_DOMINANTE']}</b> ({item['FIABILIDAD_POS']}% cons.)<br>
                Ciclo: ~{item['CICLO_DIAS']}d | <b>Atrás: {item['DIAS_ATRASO']} días</b>
                </span>
            </td>
        </tr>
        """
    return html


html_filas_24h = generar_filas_html_24h(df_det_24h)
html_filas_3d = generar_filas_html_3d(df_det_3d)
html_filas_quirurgicas = generar_filas_quirurgicas(resultados_quirurgicos)

html_plantilla = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Sistema Triple: Precisión Quirúrgica</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f4f6f9; color: #1e293b; padding: 15px; margin: 0; width: 100vw; height: 100vh; overflow-x: hidden; }
        .main-container { max-width: 100%; margin: auto; }
        .titulo-seccion { text-align: center; margin-bottom: 15px; }
        .titulo-seccion h2 { color: #0f172a; font-size: 20px; margin: 0 0 5px 0; }
        .titulo-seccion p { color: #64748b; font-size: 12px; margin: 0; }
        
        .grid-triple { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; width: 100%; }
        .card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); display: flex; flex-direction: column; height: calc(100vh - 100px); }
        
        .header-p1 { border-bottom: 2px solid #0ea5e9; padding-bottom: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .header-p2 { border-bottom: 2px solid #8b5cf6; padding-bottom: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .header-p3 { border-bottom: 2px solid #4f46e5; padding-bottom: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        
        .table-responsive { flex-grow: 1; overflow-y: auto; border: 1px solid #f1f5f9; border-radius: 6px; }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 12px; }
        th { background: #f8fafc; position: sticky; top: 0; z-index: 1; border-bottom: 2px solid #e2e8f0; color: #475569; font-size: 11px; padding: 10px; }
        .buscador { padding: 5px 8px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 11px; width: 130px; outline: none; background: #fdfdfd; }
        
        @media (max-width: 1400px) { .grid-triple { grid-template-columns: 1fr; } .card { height: auto; max-height: 550px; } }
    </style>
</head>
<body>

    <div class="main-container">
        <div class="titulo-seccion">
            <h2>🎯 SISTEMA DE PRECISIÓN QUIRÚRGICA (BLINDAJE DE HOY)</h2>
            <p>Filtro anti-salidos de ayer | Ciclos maduros para el disparo actual</p>
        </div>

        <div class="grid-triple">
            <!-- PANEL 1 -->
            <div class="card">
               <div class="header-p1">
                   <h3 style="margin: 0; color: #0284c7; font-size: 12px; text-transform: uppercase; font-weight: 700;">⏱️ ÚLTIMO DÍA (<span style="color:#0f172a;">REPLACE_FECHA_24H</span>)</h3>
                   <div><input type="text" id="filtro-24h" class="buscador" placeholder="Núm..." onkeyup="filtrar24h()"></div>
               </div>
               <div class="table-responsive">
                   <table id="tabla-24h">
                       <thead><tr><th style="width: 20%;">NÚM</th><th style="width: 20%; text-align: center;">REP</th><th style="width: 60%;">DETALLES</th></tr></thead>
                       <tbody>REPLACE_24H</tbody>
                   </table>
               </div>
            </div>

            <!-- PANEL 2 -->
            <div class="card">
               <div class="header-p2">
                   <h3 style="margin: 0; color: #7e22ce; font-size: 12px; text-transform: uppercase; font-weight: 700;">📅 3 DÍAS</h3>
                   <div><input type="text" id="filtro-3d" class="buscador" placeholder="Núm, fecha..." onkeyup="filtrar3d()"></div>
               </div>
               <div class="table-responsive">
                   <table id="tabla-3d">
                       <thead><tr><th style="width: 20%;">NÚM</th><th style="width: 20%; text-align: center;">REP</th><th style="width: 60%;">DETALLES</th></tr></thead>
                       <tbody>REPLACE_3D</tbody>
                   </table>
               </div>
            </div>

            <!-- PANEL 3: PRECISIÓN QUIRÚRGICA -->
            <div class="card">
               <div class="header-p3">
                   <h3 style="margin: 0; color: #4f46e5; font-size: 12px; text-transform: uppercase; font-weight: 700;">⚡ PRECISIÓN QUIRÚRGICA (IPM)</h3>
                   <div><input type="text" id="filtro-certeza" class="buscador" placeholder="Núm o posición..." onkeyup="filtrarCerteza()"></div>
               </div>
               <div class="table-responsive">
                   <table id="tabla-certeza">
                       <thead><tr><th style="width: 20%;">NÚM</th><th style="width: 25%; text-align: center;">IPM</th><th style="width: 55%;">ANÁLISIS QUIRÚRGICO</th></tr></thead>
                       <tbody>REPLACE_CERTEZA</tbody>
                   </table>
               </div>
            </div>
        </div>
    </div>

    <script>
        function filtrar24h() {
            let filtro = document.getElementById('filtro-24h').value.toLowerCase().trim();
            let filas = document.getElementById('tabla-24h').getElementsByClassName('fila-numero');
            for (let i = 0; i < filas.length; i++) {
                let num = filas[i].getAttribute('data-busqueda') || '';
                filas[i].style.display = (num.indexOf(filtro) !== -1 || filtro === '') ? "" : "none";
            }
        }
        function filtrar3d() {
            let filtro = document.getElementById('filtro-3d').value.toLowerCase().trim();
            let filas = document.getElementById('tabla-3d').getElementsByClassName('fila-numero-3d');
            for (let i = 0; i < filas.length; i++) {
                let fila = filas[i];
                let badges = fila.getElementsByClassName('badge-aparicion');
                let visiblesCount = 0;
                let numFila = fila.getAttribute('data-numero') || '';
                if (filtro === '') {
                    fila.style.display = '';
                    for (let b = 0; b < badges.length; b++) { badges[b].style.display = 'inline-block'; }
                    let contador = fila.getElementsByClassName('contador-freq')[0];
                    if (contador) contador.innerText = badges.length + 'v';
                    continue;
                }
                for (let b = 0; b < badges.length; b++) {
                    let badge = badges[b];
                    let meta = badge.getAttribute('data-filtro') || '';
                    if (meta.indexOf(filtro) !== -1 || numFila.indexOf(filtro) !== -1) {
                        badge.style.display = 'inline-block';
                        visiblesCount++;
                    } else { badge.style.display = 'none'; }
                }
                if (visiblesCount > 0) {
                    fila.style.display = '';
                    let contador = fila.getElementsByClassName('contador-freq')[0];
                    if (contador) contador.innerText = visiblesCount + 'v';
                } else { fila.style.display = 'none'; }
            }
        }
        function filtrarCerteza() {
            let filtro = document.getElementById('filtro-certeza').value.toLowerCase().trim();
            let filas = document.getElementById('tabla-certeza').getElementsByClassName('fila-certeza');
            for (let i = 0; i < filas.length; i++) {
                let meta = filas[i].getAttribute('data-busqueda') || '';
                filas[i].style.display = (meta.indexOf(filtro) !== -1 || filtro === '') ? "" : "none";
            }
        }
    </script>
</body>
</html>
"""

html_completo = (
    html_plantilla.replace("REPLACE_24H", html_filas_24h)
    .replace("REPLACE_3D", html_filas_3d)
    .replace("REPLACE_CERTEZA", html_filas_quirurgicas)
    .replace("REPLACE_FECHA_24H", f_24h_exacta.strftime("%d/%m/%Y"))
)

with open("reporte_externo_48h_7d.html", "w", encoding="utf-8") as f:
    f.write(html_completo)

print(
    f"\n{VERDE}¡Sistema de Precisión Quirúrgica generado exitosamente en"
    f" 'reporte_externo_48h_7d.html'!{RESET}"
)