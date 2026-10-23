import streamlit as st
import pandas as pd
import json
import os
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types

# Configuración de la página
st.set_page_config(
    page_title="Agente Capturador de Reportes",
    page_icon="🤖",
    layout="wide"
)

# Archivo local para almacenar las reglas dinámicas del agente
ARCHIVO_REGLAS = "reglas_agente.txt"

# Función para cargar reglas
def cargar_reglas():
    if os.path.exists(ARCHIVO_REGLAS):
        with open(ARCHIVO_REGLAS, "r", encoding="utf-8") as f:
            return f.read()
    return "Sin reglas adicionales definidas aún."

# Función para guardar nuevas reglas
def guardar_reglas(nueva_regla):
    reglas_actuales = cargar_reglas()
    with open(ARCHIVO_REGLAS, "w", encoding="utf-8") as f:
        if "Sin reglas adicionales" in reglas_actuales:
            f.write(f"- {nueva_regla}\n")
        else:
            f.write(f"{reglas_actuales}\n- {nueva_regla}\n")

st.title("🤖 Agente Capturador: Ventas e Inventarios")
st.caption("Herramienta inteligente de extracción, normalización y diagnóstico de reportes")

# Sidebar para Configuración y Reglas Dinámicas
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input("Gemini API Key", type="password", help="Ingresa tu API Key de Google AI Studio")
    
    st.markdown("---")
    st.header("🧠 Memoria de Reglas del Agente")
    st.caption("Instrucciones acumuladas para afinar la precisión del agente.")

    reglas_actuales = cargar_reglas()
    st.text_area("Reglas activas:", value=reglas_actuales, height=150, disabled=True)

    # Campo para agregar nueva regla al vuelo
    nueva_regla_input = st.text_input("Agregar nueva regla o corrección:")
    if st.button("💾 Guardar Regla"):
        if nueva_regla_input:
            guardar_reglas(nueva_regla_input)
            st.success("¡Regla guardada con éxito!")
            st.rerun()
        else:
            st.warning("Escribe una regla antes de guardar.")

# Tipo de reporte a procesar
tipo_reporte = st.radio(
    "Selecciona el tipo de documento:",
    ["Reporte de Ventas", "Reporte de Inventarios"],
    horizontal=True
)

# Carga de múltiples imágenes (sin mostrarlas visualmente)
uploaded_files = st.file_uploader(
    "Carga, arrastra o pega tus imágenes aquí (JPG, PNG)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    help="Puedes seleccionar varias imágenes a la vez."
)

if uploaded_files:
    st.subheader("📊 Datos Extraídos y Diagnóstico")
    
    if not api_key:
        st.warning("⚠️ Ingresa tu Gemini API Key en el menú lateral para procesar los documentos.")
    else:
        if st.button("🚀 Procesar, Analizar y Extraer", type="primary"):
            with st.spinner("El Agente está analizando las imágenes y generando su bitácora..."):
                try:
                    # Inicializar cliente de Gemini
                    client = genai.Client(api_key=api_key)
                    
                    # Recuperar reglas actuales para inyectarlas al prompt
                    reglas_dinamicas = cargar_reglas()

                    # Cargar todas las imágenes usando PIL
                    images = [Image.open(file) for file in uploaded_files]

                    # Prompt estructurado que pide un JSON con dos partes: la bitácora y los datos
                    if tipo_reporte == "Reporte de Ventas":
                        prompt_instrucciones = f"""
                        Analiza las imágenes adjuntas correspondientes a un reporte de ventas de gasolinera.
                        
                        Sigue estrictamente estas reglas acumuladas de negocio:
                        {reglas_dinamicas}

                        Devuelve tu respuesta ÚNICAMENTE en un formato JSON válido con esta estructura exacta:
                        {{
                          "diagnostico": {{
                            "resumen": "Breve explicación de qué encontraste, si la calidad fue buena, si hubo datos confusos o si todo está en orden.",
                            "conflictos_o_faltantes": "Menciona si hubo algún dato faltante, celda borrosa o si tuviste que inferir algo.",
                            "estado_general": "Óptimo / Con advertencias / Requiere revisión manual"
                          }},
                          "datos": [
                            {{
                              "fecha": "YYYY-MM-DD o null",
                              "estacion": "Texto o null",
                              "producto": "Texto o null",
                              "volumen_litros": 0.0,
                              "precio_unitario": 0.0,
                              "importe_total": 0.0
                            }}
                          ]
                        }}
                        """
                    else:
                        prompt_instrucciones = f"""
                        Analiza las imágenes adjuntas correspondientes a un reporte de inventario de combustibles.
                        
                        Sigue estrictamente estas reglas acumuladas de negocio:
                        {reglas_dinamicas}

                        Devuelve tu respuesta ÚNICAMENTE en un formato JSON válido con esta estructura exacta:
                        {{
                          "diagnostico": {{
                            "resumen": "Breve explicación de qué encontraste, si la calidad fue buena, si hubo datos confusos o si todo está en orden.",
                            "conflictos_o_faltantes": "Menciona si hubo algún dato faltante, celda borrosa o si tuviste que inferir algo.",
                            "estado_general": "Óptimo / Con advertencias / Requiere revisión manual"
                          }},
                          "datos": [
                            {{
                              "fecha": "YYYY-MM-DD o null",
                              "estacion": "Texto o null",
                              "tanque": "Texto o null",
                              "producto": "Texto o null",
                              "inventario_inicial_litros": 0.0,
                              "recepciones_litros": 0.0,
                              "ventas_litros": 0.0,
                              "inventario_final_litros": 0.0
                            }}
                          ]
                        }}
                        """

                    # Combinar la lista de imágenes con el texto de instrucciones en el payload de contents
                    contents_list = images + [prompt_instrucciones]

                    # Llamada a Gemini con salida JSON forzada
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=contents_list,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                    
                    # Parsear respuesta JSON
                    respuesta_completa = json.loads(response.text)
                    
                    # Extraer bitácora y datos
                    diagnostico = respuesta_completa.get("diagnostico", {})
                    datos_lista = respuesta_completa.get("datos", [])
                    
                    df = pd.DataFrame(datos_lista)

                    # MOSTRAR BITÁCORA / RESUMEN DEL AGENTE
                    st.info(f"🤖 **Bitácora del Agente:**\n\n"
                            f"- **Resumen:** {diagnostico.get('resumen', 'N/A')}\n"
                            f"- **Conflictos o Advertencias:** {diagnostico.get('conflictos_o_faltantes', 'Ninguno')}\n"
                            f"- **Estado General:** {diagnostico.get('estado_general', 'N/A')}")

                    st.success("✅ ¡Extracción completada con éxito!")
                    st.dataframe(df, use_container_width=True)

                    # Opciones de descarga
                    st.subheader("📥 Descargar Reporte")
                    c_csv, c_excel = st.columns(2)

                    # Exportar a CSV
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    c_csv.download_button(
                        label="📄 Descargar CSV",
                        data=csv_data,
                        file_name=f"reporte_extraido_{tipo_reporte.lower().replace(' ', '_')}.csv",
                        mime="text/csv"
                    )

                    # Exportar a Excel
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name="Datos Extraídos")
                    excel_data = buffer.getvalue()

                    c_excel.download_button(
                        label="📊 Descargar Excel",
                        data=excel_data,
                        file_name=f"reporte_extraido_{tipo_reporte.lower().replace(' ', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                except Exception as e:
                    st.error(f"❌ Ocurrió un error durante el procesamiento: {str(e)}")
