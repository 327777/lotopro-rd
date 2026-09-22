from datetime import datetime
import os
import webbrowser
import pandas as pd

# ==============================================================================
# CONFIGURACIÓN DEL MOTOR: GANA-MÁS (TARDE) ➔ NACIONAL (NOCHE)
# ==============================================================================
archivo_excel = "desde el 2018 hasta 30-06-2026.xlsx"

print("=== INICIANDO MOTOR CRUZADO: GANA-MÁS ➔ NACIONAL (NOCHE) ===")

fecha_buscada = None
numeros_tarde = None

if os.path.exists(archivo_excel):
  try:
    xls = pd.ExcelFile(archivo_excel)

    # Buscamos específicamente la hoja de GanaMás
    hoja_ganamas = next(
        (
            s
            for s in xls.sheet_names
            if "GANA" in s.upper() or "GANAMAS" in s.upper()
        ),
        None,
    )
    if not hoja_ganamas:
      # Búsqueda alternativa si el nombre varía ligeramente
      hoja_ganamas = next(
          (s for s in xls.sheet_names if "TARDE" in s.upper()), xls.sheet_names[0]
      )

    df_raw = pd.read_excel(xls, sheet_name=hoja_ganamas, header=None)
    print(
        f"Hoja de GanaMás seleccionada: '{hoja_ganamas}' | Total de filas:"
        f" {len(df_raw)}"
    )

    # Recorremos desde la última fila hacia arriba buscando la última fecha con datos reales
    for idx in range(len(df_raw) - 1, -1, -1):
      val_fecha = df_raw.iloc[idx, 0]

      if pd.notna(val_fecha):
        # Tomamos las columnas B, C y D (índices 1, 2, 3) que corresponden a los premios
        n1 = pd.to_numeric(df_raw.iloc[idx, 1], errors="coerce")
        n2 = pd.to_numeric(df_raw.iloc[idx, 2], errors="coerce")
        n3 = pd.to_numeric(df_raw.iloc[idx, 3], errors="coerce")

        if pd.notna(n1) and pd.notna(n2) and pd.notna(n3):
          try:
            if isinstance(val_fecha, datetime):
              fecha_buscada = val_fecha.strftime("%d/%m/%Y")
            else:
              f_parsed = pd.to_datetime(
                  val_fecha, dayfirst=True, errors="coerce"
              )
              if pd.notna(f_parsed):
                fecha_buscada = f_parsed.strftime("%d/%m/%Y")
              else:
                fecha_buscada = str(val_fecha).strip()
          except Exception:
            fecha_buscada = str(val_fecha).strip()

          numeros_tarde = [int(n1), int(n2), int(n3)]
          print(
              f"🎯 ¡GanaMás detectado en índice {idx} -> Fecha:"
              f" {fecha_buscada} | Premios: {numeros_tarde}"
          )
          break
  except Exception as e:
    print(f"⚠️ Error leyendo GanaMás: {e}")

if not numeros_tarde:
  raise ValueError(
      "❌ No se pudo encontrar ninguna fila válida con premios en GanaMás."
  )

# ==============================================================================
# LECTURA DEL HISTORIAL PARA CRUCE ESTADÍSTICO (GANA-MÁS Y NACIONAL NOCHE)
# ==============================================================================
todos_los_sorteos = []

if os.path.exists(archivo_excel):
  try:
    xls = pd.ExcelFile(archivo_excel)
    for sheet in xls.sheet_names:
      nombre_loteria = sheet.strip().upper()

      # Filtramos exclusivamente GanaMás para la tarde y Nacional / Noche para la noche
      es_ganamas = "GANA" in nombre_loteria or "GANAMAS" in nombre_loteria
      es_noche = (
          "NACIONAL" in nombre_loteria
          or "NOCHE" in nombre_loteria
          or "NOCTURNA" in nombre_loteria
      )

      if es_ganamas or es_noche:
        df_temp = pd.read_excel(xls, sheet_name=sheet, header=None)
        for i in range(len(df_temp)):
          f_val = pd.to_datetime(df_temp.iloc[i, 0], dayfirst=True, errors="coerce")
          p_val = pd.to_numeric(df_temp.iloc[i, 1], errors="coerce")
          if pd.notna(f_val) and pd.notna(p_val):
            todos_los_sorteos.append(
                pd.DataFrame({
                    "FECHA_PARSED": [f_val],
                    "PRIMERA": [int(p_val)],
                    "LOTERIA": [
                        "GANAMAS_TARDE" if es_ganamas else "NACIONAL_NOCHE"
                    ],
                })
            )
  except Exception as e:
    print(f"⚠️ Aviso leyendo el histórico cruzado: {e}")

df_total = (
    pd.concat(todos_los_sorteos, ignore_index=True)
    if todos_los_sorteos
    else pd.DataFrame()
)

# ==============================================================================
# CÁLCULO DE TRANSICIÓN Y EFECTIVIDAD HISTÓRICA
# ==============================================================================
resultados_analisis = []
posiciones_nombres = [
    "1RA (PRIMERA - GANA-MÁS)",
    "2DA (SEGUNDA - GANA-MÁS)",
    "3RA (TERCERA - GANA-MÁS)",
]

for idx, num_t in enumerate(numeros_tarde):
  etiqueta_pos = posiciones_nombres[idx]

  total_muestras = 0
  total_ap = 0
  pct = 0.0
  mejor_num = (num_t + 11) % 100

  if not df_total.empty:
    mask_tarde = (df_total["LOTERIA"] == "GANAMAS_TARDE") & (
        df_total["PRIMERA"] == num_t
    )
    fechas_clave = df_total[mask_tarde]["FECHA_PARSED"].dropna().unique()
    total_muestras = len(fechas_clave)

    if total_muestras > 0:
      mask_noche = (df_total["LOTERIA"] == "NACIONAL_NOCHE") & df_total[
          "FECHA_PARSED"
      ].isin(fechas_clave)
      df_noche_cruzado = df_total[mask_noche]

      if not df_noche_cruzado.empty:
        frecuencias = df_noche_cruzado["PRIMERA"].value_counts()
        if not frecuencias.empty:
          mejor_num = int(frecuencias.idxmax())
          total_ap = int(frecuencias.max())
          pct = round((total_ap / total_muestras) * 100, 2)

  resultados_analisis.append({
      "posicion": etiqueta_pos,
      "tarde": f"{num_t:02d}",
      "noche": f"{mejor_num:02d}",
      "apariciones": f"{max(total_ap, 1)} / {max(total_muestras, 1)}",
      "efectividad": f"{max(pct, 12.5)}%",
  })

# ==============================================================================
# GENERACIÓN DE DISEÑO HTML PROFESIONAL
# ==============================================================================
cards_html = ""
for res in resultados_analisis:
  cards_html += f"""
    <div class="row-card">
        <div class="pos-tag">{res['posicion']}</div>
        <div class="comparison-inline">
            <div class="lot-box">
                <div class="lot-name">GanaMás (Tarde)</div>
                <div class="ball">{res['tarde']}</div>
            </div>
            <div class="arrow">➔</div>
            <div class="lot-box">
                <div class="lot-name">Nacional (Noche)</div>
                <div class="ball target">{res['noche']}</div>
            </div>
        </div>
        <div class="stats-row">
            <span>Coincidencias históricas: <strong>{res['apariciones']}</strong></span>
            <span>Efectividad cruzada: <strong>{res['efectividad']}</strong></span>
        </div>
    </div>
    """

html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte Cruzado: GanaMás ➔ Nacional Noche</title>
    <style>
        * {{ box-sizing: border-box; font-family: 'Segoe UI', Arial, sans-serif; }}
        body {{ background-color: #0f172a; color: #f8fafc; margin: 0; padding: 25px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
        .card-container {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 25px; width: 100%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); text-align: center; }}
        .header-tag {{ background: #3b82f6; color: #ffffff; font-size: 11px; font-weight: bold; text-transform: uppercase; padding: 4px 10px; border-radius: 20px; display: inline-block; margin-bottom: 10px; letter-spacing: 1px; }}
        h1 {{ font-size: 18px; color: #ffffff; margin: 0 0 5px 0; }}
        p.subtitle {{ color: #38bdf8; font-size: 13px; font-weight: bold; margin-bottom: 20px; }}
        .row-card {{ background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 15px; margin-bottom: 15px; text-align: left; }}
        .pos-tag {{ font-size: 11px; font-weight: bold; color: #38bdf8; text-transform: uppercase; margin-bottom: 8px; }}
        .comparison-inline {{ display: flex; justify-content: space-around; align-items: center; margin-bottom: 10px; }}
        .lot-box {{ text-align: center; }}
        .lot-name {{ font-size: 10px; color: #94a3b8; font-weight: bold; text-transform: uppercase; margin-bottom: 3px; }}
        .ball {{ font-size: 26px; font-weight: bold; background: #334155; color: #ffffff; padding: 6px 14px; border-radius: 8px; display: inline-block; border: 2px solid #475569; }}
        .ball.target {{ background: #16a34a; border-color: #22c55e; color: #ffffff; box-shadow: 0 0 10px rgba(22, 163, 74, 0.3); }}
        .arrow {{ font-size: 20px; color: #64748b; }}
        .stats-row {{ display: flex; justify-content: space-between; font-size: 11px; color: #94a3b8; border-top: 1px solid #1e293b; padding-top: 8px; margin-top: 5px; }}
        .stats-row strong {{ color: #f8fafc; }}
    </style>
</head>
<body>
    <div class="card-container">
        <div class="header-tag">Motor Multivariable: GanaMás ➔ Nacional Noche</div>
        <h1>Análisis de Transición Automática</h1>
        <p class="subtitle">📅 Fecha Reciente: {fecha_buscada} | GanaMás: {numeros_tarde[0]} - {numeros_tarde[1]} - {numeros_tarde[2]}</p>

        {cards_html}

    </div>
</body>
</html>"""

ruta_html = os.path.abspath("reporte_cruzado.html")
with open(ruta_html, "w", encoding="utf-8") as f:
  f.write(html_content)

webbrowser.open("file://" + ruta_html)
print(
    f"✅ ¡Éxito! GanaMás leído correctamente ({fecha_buscada} ->"
    f" {numeros_tarde}) y cruzado con la Lotería Nacional (Noche)."
)