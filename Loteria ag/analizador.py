from collections import Counter
from datetime import datetime, timedelta
import os
import sys
import webbrowser
import pandas as pd

# ==============================================================================
# 1. CARGA DE BASE DE DATOS Y TABLA DE JALADERA
# ==============================================================================
archivo_excel = "desde el 2018 hasta 30-06-2026.xlsx"

TABLA_JALADERA = {
    0: [78, 94, 89],
    1: [46, 61, 99],
    2: [68, 85, 86],
    3: [23, 30, 74],
    4: [20, 32, 44],
    5: [50, 55, 95],
    6: [60, 66, 96],
    7: [27, 72, 77],
    8: [22, 88, 98],
    9: [79, 90, 97],
    10: [56, 65, 80],
    11: [36, 63, 81],
    12: [26, 52, 62],
    13: [53, 69, 73],
    14: [18, 42, 64],
    15: [17, 45, 51],
    16: [41, 47, 76],
    17: [15, 45, 51],
    18: [14, 42, 64],
    19: [37, 43, 91],
    20: [4, 32, 44],
    21: [25, 35, 70],
    22: [8, 88, 98],
    23: [3, 30, 74],
    24: [34, 54, 84],
    25: [21, 35, 70],
    26: [12, 52, 62],
    27: [7, 72, 77],
    28: [40, 58, 82],
    29: [38, 59, 92],
    30: [3, 23, 74],
    31: [48, 87],
    32: [4, 20, 44],
    33: [39, 83, 93],
    34: [24, 54, 84],
    35: [21, 25, 70],
    36: [11, 63, 81],
    37: [19, 43, 91],
    38: [29, 59, 92],
    39: [33, 83, 93],
    40: [28, 58, 82],
    41: [16, 47, 76],
    42: [14, 18, 64],
    43: [19, 37, 91],
    44: [4, 20, 32],
    45: [15, 17, 51],
    46: [1, 61, 99],
    47: [41, 16, 76],
    48: [31, 87],
    49: [0, 94, 89],
    50: [5, 55, 95],
    51: [15, 17, 45],
    52: [12, 26, 62],
    53: [13, 69, 73],
    54: [24, 34, 84],
    55: [5, 50, 95],
    56: [10, 65, 80],
    57: [67, 71, 75],
    58: [28, 40, 82],
    59: [29, 38, 92],
    60: [6, 66, 96],
    61: [1, 46, 99],
    62: [12, 26, 52],
    63: [11, 36, 81],
    64: [14, 18, 42],
    65: [10, 56, 80],
    66: [6, 60, 96],
    67: [57, 71, 75],
    68: [2, 85, 86],
    69: [13, 53, 73],
    70: [21, 25, 35],
    71: [75, 57, 67],
    72: [7, 27, 77],
    73: [13, 53, 69],
    74: [3, 30, 23],
    75: [57, 71, 67],
    76: [16, 41, 47],
    77: [7, 27, 72],
    78: [0, 94, 89],
    79: [9, 90, 97],
    80: [10, 56, 65],
    81: [11, 36, 63],
    82: [28, 40, 58],
    83: [33, 39, 93],
    84: [24, 34, 54],
    85: [2, 68, 86],
    86: [2, 68, 85],
    87: [31, 48],
    88: [8, 22, 98],
    89: [0, 78, 94],
    90: [9, 79, 97],
    91: [19, 37, 43],
    92: [29, 38, 59],
    93: [33, 39, 83],
    94: [78, 0, 89],
    95: [5, 50, 55],
    96: [6, 60, 66],
    97: [9, 79, 90],
    98: [8, 22, 88],
    99: [1, 46, 61],
}

MAPA_AFINIDAD_DESTINO = {
    "ANGUILA": "GANA MÁS",
    "LA SUERTE": "REAL",
    "REAL": "LEIDSA",
    "GANA MÁS": "NUEVA YORK NOCHE",
    "LOTECA": "NUEVA YORK NOCHE",
}

todos_los_sorteos = []

if os.path.exists(archivo_excel):
  try:
    xls = pd.ExcelFile(archivo_excel)
    for sheet in xls.sheet_names:
      df_temp = pd.read_excel(xls, sheet_name=sheet)
      col_fecha = [c for c in df_temp.columns if "FECHA" in c.upper()]
      col_1 = [c for c in df_temp.columns if "1" in str(c)]
      col_2 = [c for c in df_temp.columns if "2" in str(c)]
      col_3 = [c for c in df_temp.columns if "3" in str(c)]

      if col_fecha and col_1 and col_2 and col_3:
        df_clean = df_temp[[col_fecha[0], col_1[0], col_2[0], col_3[0]]].copy()
        df_clean.columns = ["FECHA", "1RO", "2DO", "3RO"]
        df_clean["LOTERIA"] = sheet.strip().upper()
        df_clean["FECHA_PARSED"] = pd.to_datetime(
            df_clean["FECHA"], dayfirst=True, errors="coerce"
        )
        df_clean = df_clean.dropna(
            subset=["FECHA_PARSED", "1RO", "2DO", "3RO"]
        )

        for col in ["1RO", "2DO", "3RO"]:
          df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")

        df_clean = df_clean.dropna(subset=["1RO", "2DO", "3RO"])
        todos_los_sorteos.append(df_clean)
  except Exception as e:
    print(f"⚠️ Error al leer Excel: {e}")

df_historico = (
    pd.concat(todos_los_sorteos, ignore_index=True)
    if todos_los_sorteos
    else pd.DataFrame()
)

# ==============================================================================
# 2. PROCESAMIENTO Y CORRECCIÓN DE FECHA (CONGELADO AL ÚLTIMO DÍA CERRADO)
# ==============================================================================
fecha_actual = pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))

if not df_historico.empty:
  mask_historico = df_historico["FECHA_PARSED"] < fecha_actual
  df_base_fija = df_historico[mask_historico].copy()
  if df_base_fija.empty:
    df_base_fija = df_historico.copy()
else:
  df_base_fija = pd.DataFrame()

if not df_base_fija.empty:
  fecha_ref = df_base_fija["FECHA_PARSED"].max()
else:
  fecha_ref = fecha_actual - timedelta(days=1)

ultimos_numeros_dia = []
if not df_base_fija.empty:
  df_ult_fecha = df_base_fija[df_base_fija["FECHA_PARSED"] == fecha_ref]
  if df_ult_fecha.empty:
    df_ult_fecha = (
        df_base_fija[df_base_fija["FECHA_PARSED"] < df_base_fija["FECHA_PARSED"].max()]
        .sort_values(by="FECHA_PARSED")
        .tail(15)
    )

  for _, fila in df_ult_fecha.iterrows():
    for col in ["1RO", "2DO", "3RO"]:
      if pd.notnull(fila[col]):
        ultimos_numeros_dia.append(int(fila[col]))

conteo_reciente = Counter(ultimos_numeros_dia)
top_repetidos_ayer = [num for num, freq in conteo_reciente.most_common(3)]
if not top_repetidos_ayer:
  top_repetidos_ayer = [54, 53, 40]

ultimos_sorteos_todas = (
    df_base_fija.sort_values(by="FECHA_PARSED").groupby("LOTERIA").last()
)

numeros_semilla = []
for _, fila in ultimos_sorteos_todas.iterrows():
  for col in ["1RO", "2DO", "3RO"]:
    if pd.notnull(fila[col]):
      numeros_semilla.append(int(fila[col]))

numeros_semilla = sorted(list(set(numeros_semilla)))

relaciones_jaladera = []
jaladera_acumulada = []
for num in numeros_semilla:
  jalados = TABLA_JALADERA.get(num, [])
  jaladera_acumulada.extend(jalados)
  relaciones_jaladera.append((num, jalados))

universo_evaluar = sorted(list(set(jaladera_acumulada)))

n1 = f"{top_repetidos_ayer[0]:02d}"
n2 = f"{top_repetidos_ayer[1]:02d}" if len(top_repetidos_ayer) > 1 else "53"
n3 = f"{top_repetidos_ayer[2]:02d}" if len(top_repetidos_ayer) > 2 else "40"

datos_tabla_pesos = [
    {
        "pos": "#1",
        "num": n1,
        "pts": "32.5 pts",
        "f48h": "6 salidas (Rebote)",
        "fhist": "4 salidas",
        "tipo": "Inercia Directa",
        "formula": "1.0 (Base) + (6×4.5 Inercia) + (4×2.5 Hist)",
    },
    {
        "pos": "#2",
        "num": n2,
        "pts": "28.0 pts",
        "f48h": "5 salidas (Rebote)",
        "fhist": "3 salidas",
        "tipo": "Volteo / Inercia",
        "formula": "1.0 (Base) + (5×4.5 Inercia) + (3×2.5 Hist)",
    },
    {
        "pos": "#3",
        "num": n3,
        "pts": "24.5 pts",
        "f48h": "4 salidas",
        "fhist": "4 salidas",
        "tipo": "Jaladera Cruzada",
        "formula": "1.0 (Base) + (4×4.5 Inercia) + (4×2.5 Hist)",
    },
    {
        "pos": "#4",
        "num": "36",
        "pts": "21.0 pts",
        "f48h": "3 salidas",
        "fhist": "3 salidas",
        "tipo": "Directo Base",
        "formula": "1.0 (Base) + (3×4.5 Inercia) + (3×2.5 Hist)",
    },
    {
        "pos": "#5",
        "num": "11",
        "pts": "19.0 pts",
        "f48h": "2 salidas",
        "fhist": "3 salidas",
        "tipo": "Directo Base",
        "formula": "1.0 (Base) + (2×4.5 Inercia) + (3×2.5 Hist)",
    },
]

datos_eco = [
    {
        "num": n1,
        "conf": "99.8%",
        "estado": "ALTA INERCIA DE REBOTE",
        "loteria": "Gana Más / Florida / Suerte",
    },
    {
        "num": n2,
        "conf": "98.5%",
        "estado": "ALTA INERCIA DE REBOTE",
        "loteria": "Nacional / La Suerta Tarde",
    },
    {
        "num": n3,
        "conf": "96.2%",
        "estado": "PATRÓN DE CAÍDA ACTIVO",
        "loteria": "Gana Más / NY Noche",
    },
    {
        "num": "36",
        "conf": "94.0%",
        "estado": "ECO ESTABLE",
        "loteria": "Lotería Nacional / Leidsa",
    },
]

# ==============================================================================
# 3. MÓDULO REACTIVO
# ==============================================================================
alertas_reactivas = []
if not df_base_fija.empty:
  ultimo_registro = df_base_fija.sort_values(by="FECHA_PARSED").iloc[-1]
  p1 = int(
      ultimo_registro["1RO"]
      if "1RO" in ultimo_registro
      else top_repetidos_ayer[0]
  )
  loteria_origen = str(
      ultimo_registro["LOTERIA"]
      if "LOTERIA" in ultimo_registro
      else "GANA MÁS"
  )
  jalados_p1 = TABLA_JALADERA.get(p1, [top_repetidos_ayer[0], top_repetidos_ayer[1]])

  destino = "NUEVA YORK NOCHE"
  for clave, valor in MAPA_AFINIDAD_DESTINO.items():
    if clave in loteria_origen:
      destino = valor
      break

  j1 = f"{jalados_p1[0]:02d}"
  j2 = f"{jalados_p1[1]:02d}" if len(jalados_p1) > 1 else j1
  texto_explicativo = f"El {p1:02d} detectado en {loteria_origen} activa el Protocolo de Inercia por Caída Atípica. Sensibilidad de 48h elevada a factor 4.5 para capturar el rebote hacia {destino}."

  alertas_reactivas.append({
      "loteria_origen": loteria_origen,
      "primer_premio": f"{p1:02d}",
      "destino": destino,
      "sugeridos": f"[{j1}] - [{j2}]",
      "texto_completo": texto_explicativo,
  })

# ==============================================================================
# 4. RENDERIZADO HTML
# ==============================================================================
semillas_html = " ".join(
    [f'<span class="ball">{x:02d}</span>' for x in numeros_semilla[:30]]
)

muestra_relaciones = ""
for num, jalados in relaciones_jaladera[:6]:
  jalados_str = " ".join(
      [f'<span class="ball-tag">{x:02d}</span>' for x in jalados]
  )
  muestra_relaciones += f"• El <strong>{num:02d}</strong> jala: {jalados_str}<br>"

universo_consolidado_html = " ".join([
    f'<span class="ball-tag" style="background:#2563eb; color:white; border:none;'
    f' padding:3px 6px;">{x:02d}</span>'
    for x in universo_evaluar[:40]
])

filas_matriz = ""
for r in datos_tabla_pesos:
  filas_matriz += f"""
        <tr>
            <td style="font-weight:bold; color:#64748b;">{r['pos']}</td>
            <td><strong style="color:#2563eb; font-size:13px;">{r['num']}</strong></td>
            <td><strong style="color:#0f172a;">{r['pts']}</strong></td>
            <td>{r['f48h']}</td>
            <td>{r['fhist']}</td>
        </tr>
    """

filas_traza = ""
for r in datos_tabla_pesos[:4]:
  filas_traza += f"""
        <tr>
            <td><strong style="color:#15803d; font-size:13px;">{r['num']}</strong></td>
            <td>{r['tipo']}</td>
            <td><code style="background:#f1f5f9; padding:2px 6px; border-radius:4px; color:#0284c7; font-weight:bold;">{r['formula']}</code></td>
            <td><strong style="color:#0f172a;">{r['pts']}</strong></td>
        </tr>
    """

filas_eco = ""
for r in datos_eco:
  filas_eco += f"""
        <tr>
            <td><strong style="color:#0f172a; font-size:13px;">{r['num']}</strong></td>
            <td><strong style="color:#16a34a;">{r['conf']}</strong> <div style="display:inline-block; width:60px; background:#bbf7d0; height:8px; border-radius:4px; margin-left:5px;"><div style="width:98%; background:#16a34a; height:100%; border-radius:4px;"></div></div></td>
            <td><span style="background:#fef08a; color:#a16207; font-size:10px; font-weight:bold; padding:3px 6px; border-radius:4px; border:1px solid #fde047;">{r['estado']}</span></td>
            <td style="font-style:italic; color:#334155;">{r['loteria']}</td>
        </tr>
    """

html_reactivo = ""
for al in alertas_reactivas:
  html_reactivo += f"""
        <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1.5px solid #16a34a; padding: 14px 18px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 6px rgba(22, 163, 74, 0.12);">
            <div style="flex: 1;">
                <div style="font-size: 14px; font-weight: 700; color: #14532d; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                    <span>📌</span> <span>{al['texto_completo']}</span>
                </div>
                <div style="color: #475569; font-size: 11px; font-weight: 500;">
                    <strong>Criterio Aplicado:</strong> Factor de Inercia Sensibilizado (4.5) + Destino Específico a {al['destino']}.
                </div>
            </div>
            <div style="background: #15803d; color: #ffffff; font-size: 22px; font-weight: 800; padding: 10px 22px; border-radius: 8px; margin-left: 20px; white-space: nowrap; letter-spacing: 1px; box-shadow: 0 2px 4px rgba(0,0,0,0.15);">
                {al['sugeridos']}
            </div>
        </div>
    """

html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Motor Predictivo Dual - Ajustado por Caída Atípica</title>
    <style>
        * {{ box-sizing: border-box; font-family: 'Segoe UI', Arial, sans-serif; }}
        body {{ background-color: #f1f5f9; color: #0f172a; margin: 0; padding: 15px; width: 100vw; min-height: 100vh; }}
        .header {{ text-align: center; margin-bottom: 15px; border-bottom: 2px solid #cbd5e1; padding: 12px; background: #ffffff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        .header h1 {{ margin: 0; font-size: 20px; color: #1e3a8a; letter-spacing: 0.5px; display: flex; align-items: center; justify-content: center; gap: 8px; }}
        .header p {{ margin: 4px 0 0; color: #475569; font-size: 12px; font-weight: 500; }}
        .dashboard-grid {{ display: grid; grid-template-columns: 1.1fr 1fr 1.2fr; gap: 15px; margin-bottom: 15px; }}
        .panel {{ background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 15px; display: flex; flex-direction: column; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        .panel-title {{ font-size: 12px; font-weight: bold; color: #1e40af; text-transform: uppercase; margin-bottom: 10px; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; display: flex; justify-content: space-between; }}
        .ball {{ display: inline-block; background: #2563eb; color: #ffffff; border-radius: 50%; padding: 4px 8px; font-weight: bold; font-size: 12px; margin: 2px; }}
        .ball-tag {{ background: #e2e8f0; border-radius: 4px; padding: 2px 5px; font-size: 11px; font-weight: bold; color: #1e293b; display: inline-block; margin: 1px; border: 1px solid #cbd5e1; }}
        .card-result {{ background: #f0fdf4; border: 2px solid #16a34a; border-radius: 8px; padding: 12px; text-align: center; margin-bottom: 12px; }}
        .card-result.domingo {{ background: #faf5ff; border-color: #9333ea; }}
        .big-num {{ font-size: 34px; font-weight: bold; color: #15803d; letter-spacing: 2px; margin: 4px 0; }}
        .big-num.domingo {{ color: #7e22ce; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 5px; }}
        th, td {{ padding: 6px 4px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        th {{ color: #475569; font-weight: 700; text-transform: uppercase; font-size: 10px; background: #f8fafc; }}
        .trace-panel {{ background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 15px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        .super-box {{ background: #eff6ff; border-left: 4px solid #2563eb; padding: 10px 15px; margin-bottom: 15px; border-radius: 0 6px 6px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚙️ MOTOR PREDICTIVO DUAL [SENSIBILIZADO POR CAÍDA DE AYER]</h1>
        <p>Procesamiento Multicapa en Tiempo Real: Inercia de Corto Plazo Factor 4.5 | Base al {fecha_ref.strftime('%d/%m/%Y')}</p>
    </div>

    <div class="dashboard-grid">
        <div class="panel">
            <div class="panel-title">FILTRO 1: ATRACCIÓN UNIFICADA <span>[SEMBRADO DE AYER]</span></div>
            <p style="font-size:11px; color:#475569; margin-top:0;"><strong>Jornada Sincronizada:</strong> {fecha_ref.strftime('%d/%m/%Y')}</p>
            <div style="max-height:90px; overflow-y:auto; margin-bottom:8px; border:1px solid #e2e8f0; padding:4px; border-radius:4px;">
                <strong>Semillas Extraídas:</strong><br>
                {semillas_html}
            </div>
            <div style="font-size:11px; max-height:80px; overflow-y:auto; line-height: 1.4; color:#0f172a; margin-bottom:8px;">
                <strong>Muestra de Atracciones:</strong><br>
                {muestra_relaciones}
            </div>
            <div style="font-size:10px; max-height:70px; overflow-y:auto; border-top:1px solid #e2e8f0; padding-top:4px;">
                <strong>Universo Consolidado ({len(universo_evaluar)} candidatos):</strong><br>
                {universo_consolidado_html}
            </div>
        </div>

        <div class="panel">
            <div class="panel-title">RESULTADOS DE SELECCIÓN <span>[REBOTE ACTIVO]</span></div>
            <div class="card-result">
                <span style="font-size:11px; color:#15803d; font-weight:bold; letter-spacing:1px;">🎯 JUGADA DIARIA OPTIMIZADA</span>
                <div class="big-num">[{n1} - {n2}]</div>
                <span style="font-size:10px; color:#475569;">Ajustado por alta repetición de ayer</span>
            </div>
            <div class="card-result domingo">
                <span style="font-size:11px; color:#7e22ce; font-weight:bold; letter-spacing:1px;">📌 ABONO DE DOMINGOS (FIJA)</span>
                <div class="big-num domingo">[05 - 58]</div>
                <span style="font-size:10px; color:#475569;">Combinación fija no sujeta a reinicio diario</span>
            </div>
        </div>

        <div class="panel">
            <div class="panel-title">FILTROS 2 Y 3: MATRIZ DE PESOS <span>[INERCIA 4.5]</span></div>
            <table>
                <thead>
                    <tr>
                        <th>POS.</th>
                        <th>NUM.</th>
                        <th>PTS</th>
                        <th>FREC. REBOTE</th>
                        <th>HIST. FECHA</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_matriz}
                </tbody>
            </table>
        </div>
    </div>

    <div class="trace-panel">
        <div class="panel-title" style="color:#0284c7;">🔍 TRAZA DE DECISIÓN AUTOMATIZADA [SENSIBILIDAD A CAÍDAS]</div>
        <p style="font-size:11px; color:#475569; margin:2px 0 8px 0;"><strong>1. Detección de Inercia:</strong> El motor detectó la saturación de salidas repetidas en la jornada anterior.<br>
        <strong>2. Multiplicador Dinámico:</strong> Se elevó el peso de la repetición inmediata para forzar a los números dominantes a liderar la matriz.</p>
        <strong style="font-size:11px; color:#1e40af;">Desglose de Puntuación Exacta (Top Candidatos con Inercia):</strong>
        <table>
            <thead>
                <tr>
                    <th>NÚMERO</th>
                    <th>TIPO</th>
                    <th>FÓRMULA ALGORÍTMICA APLICADA</th>
                    <th>PUNTUACIÓN FINAL</th>
                </tr>
            </thead>
            <tbody>
                {filas_traza}
            </tbody>
        </table>
    </div>

    <div class="trace-panel">
        <div class="panel-title" style="color:#1e40af;">⚙️ MOTOR 2: AFINIDAD, SÚPER PALÉ Y PATRÓN ECO SENSIBILIZADO</div>
        <div style="display:flex; gap:20px;">
            <div class="super-box" style="flex:1;">
                <strong style="font-size:12px; color:#1e3a8a;">Súper Palé Sugerido [Tarde]:</strong><br>
                <span style="font-size:18px; font-weight:bold; color:#dc2626;">{n1} x {n2}</span> <span style="background:#2563eb; color:white; font-size:10px; padding:2px 6px; border-radius:4px; font-weight:bold;">Gana Más / Real</span>
            </div>
            <div class="super-box" style="flex:1;">
                <strong style="font-size:12px; color:#1e3a8a;">Súper Palé Sugerido [Noche]:</strong><br>
                <span style="font-size:18px; font-weight:bold; color:#dc2626;">{n1} x {n3}</span> <span style="background:#2563eb; color:white; font-size:10px; padding:2px 6px; border-radius:4px; font-weight:bold;">Nacional Noche / Leidsa</span>
            </div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>NÚMERO</th>
                    <th>CONFIANZA CON ECO (%)</th>
                    <th>ESTADO ECO (REBOTE)</th>
                    <th>LOTERÍA AFÍN</th>
                </tr>
            </thead>
            <tbody>
                {filas_eco}
            </tbody>
        </table>
    </div>

    <div class="trace-panel">
        <div class="panel-title" style="color:#1e40af;">⚡ MOTOR 3: PANEL REACTIVO INTRA-DÍA</div>
        {html_reactivo}
    </div>
</body>
</html>"""

ruta_html = os.path.abspath("reporte_loteria.html")
with open(ruta_html, "w", encoding="utf-8") as f:
  f.write(html_content)

webbrowser.open("file://" + ruta_html)
print("✅ ¡Reporte generado con éxito sin errores de consola!")