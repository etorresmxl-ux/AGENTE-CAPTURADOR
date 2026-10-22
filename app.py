import streamlit as st
import pandas as pd
import json
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

st.title("🤖 Agente Capturador: Ventas e Inventarios")
st.caption("Herramienta de extracción y normalización de reportes desde imágenes")

# Sidebar para API Key de Gemini
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input("Gemini API Key", type="password", help="Ingresa tu API Key de Google AI Studio")
    st.markdown("---")
    st.info("Sube una imagen o foto de un reporte de ventas o inventario para extraer los datos de forma estructurada.")

# Tipo de reporte a procesar
tipo_reporte = st.radio(
    "Selecciona el tipo de documento:",
    ["Reporte de Ventas", "Reporte de Inventarios"],
    horizontal=True
)

# Carga de la imagen
uploaded_file = st.file_uploader(
    "Carga la imagen del reporte (JPG, PNG)", 
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    # Mostrar vista previa de la imagen
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🖼️ Documento Cargado")
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)

    with col2:
        st.subheader("📊 Datos Extraídos y Normalizados")
        
        if not api_key:
            st.warning("⚠️ Ingresa tu Gemini API Key en el menú lateral para procesar el documento.")
        else:
            if st.button("🚀 Procesar y Extraer Datos", type="primary"):
                with st.spinner("El Agente está analizando la imagen..."):
                    try:
                        # Inicializar cliente de Gemini
                        client = genai.Client(api_key=api_key)
                        
                        # Definir Prompt de extracción según el tipo de reporte
                        if tipo_reporte == "Reporte de Ventas":
                            prompt_instrucciones = """
                            Analiza la imagen adjunta correspondiente a un reporte de ventas de gasolinera.
                            Extrae la información y devuélvela estrictamente en un formato JSON valido (una lista de objetos/filas).
                            Cada objeto debe contener exactamente estas claves (si algún dato no existe, pon null):
                            - fecha: YYYY-MM-DD
                            - estacion: Nombre o número de la estación
                            - producto: Magna, Premium, Diesel, etc.
                            - volumen_litros: Número flotante de litros vendidos
                            - precio_unitario: Número flotante del precio por litro
                            - importe_total: Número flotante del total cobrado
                            """
                        else:
                            prompt_instrucciones = """
                            Analiza la imagen adjunta correspondiente a un reporte de inventario de combustibles.
                            Extrae la información y devuélvela estrictamente en un formato JSON valido (una lista de objetos/filas).
                            Cada objeto debe contener exactamente estas claves (si algún dato no existe, pon null):
                            - fecha: YYYY-MM-DD
                            - estacion: Nombre o número de la estación
                            - tanque: Identificador o número de tanque
                            - producto: Magna, Premium, Diesel, etc.
                            - inventario_inicial_litros: Número flotante
                            - recepciones_litros: Número flotante
                            - ventas_litros: Número flotante
                            - inventario_final_litros: Número flotante
                            """

                        # Llamada a Gemini con salida JSON forzada
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[image, prompt_instrucciones],
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json"
                            )
                        )
                        
                        # Parsear respuesta JSON a pandas DataFrame
                        datos_json = json.loads(response.text)
                        df = pd.DataFrame(datos_json)

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
