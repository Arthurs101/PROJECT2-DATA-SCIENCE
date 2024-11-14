import streamlit as st
from datetime import datetime
import os
from InteractiveModels import predict  # Import the prediction function
import torch
import tempfile

# Configuración de la sesión para la navegación
if "page" not in st.session_state:
    st.session_state.page = "diagnostico_lumbar"  # Página principal

# Función para cambiar de página
def cambiar_pagina(pagina):
    st.session_state.page = pagina

# CSS para estilos personalizados
st.markdown("""
    <style>            
        .input-field {
            background-color: #a3e4f9;
            border-radius: 20px;
            color: black;
            font-size: 18px;
            height: 45px;
            width: 100%;
            text-align: center;
            margin-bottom: 10px;
        }
        .upload-button {
            border-radius: 20px;
            background-color: #a3e4f9;
            color: black;
            font-size: 18px;
            height: 45px;
            width: 100%;
            margin-bottom: 10px;
        }
        .submit-button {
            background-color: #a3e4f9;
            color: black;
            font-size: 18px;
            border-radius: 20px;
            width: 100%;
            margin-top: 10px;
        }
        .navbar {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 80px;
            background-color: #f0f0f0;
            display: flex;
            justify-content: space-around;
            align-items: center;
            box-shadow: 0 -2px 5px rgba(0,0,0,0.15);
            z-index: 9999;
        }
        .navbar a {
            text-decoration: none;
            color: inherit;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 70px;
            height: 70px;
            transition: background-color 0.3s ease;
        }
        .navbar a:hover {
            background-color: #e0e0e0;
            border-radius: 50%;
        }
        .navbar img {
            width: 50px;
            height: 50px;
        }
        .centered-title {
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .centered-image {
            display: block;
            margin: 0 auto 20px auto;
            width: 150px;
        }
        .card {
            box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
            transition: 0.3s;
            width: 100%;
            margin-bottom: 20px;
        }
        .card:hover {
            box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
        }
        .container {
            padding: 2px 16px;
        }
    </style>
""", unsafe_allow_html=True)

# Página para registrar al paciente
def registrar_paciente():
    st.markdown("<div class='centered-title'>Agregar paciente</div>", unsafe_allow_html=True)
    st.markdown("<img src='https://images.vexels.com/media/users/3/200356/isolated/preview/127d177d9fda573481055d66bc602942-simbolo-del-caduceo-monocromo.png' class='centered-image'>", unsafe_allow_html=True)
    nombre_paciente = st.text_input("Nombre del paciente:", "", placeholder="Nombre del paciente", help="Ingrese el nombre del paciente")

    if nombre_paciente:
        ruta_paciente = f"./Images/{nombre_paciente.replace(' ', '_')}"
        if os.path.exists(ruta_paciente):
            st.warning("El paciente ya está registrado.")
        else:
            os.makedirs(ruta_paciente, exist_ok=True)
            st.success(f"Paciente '{nombre_paciente}' registrado exitosamente.")
            st.session_state["nombre_paciente"] = nombre_paciente

# Página para subir imagen de diagnóstico
def diagnostico_lumbar():
    st.markdown("<div class='centered-title'>Registro diagnóstico lumbar</div>", unsafe_allow_html=True)
    nombre_paciente = st.text_input("Nombre del paciente:", "", placeholder="Nombre del paciente")
    imagen_diagnostico = st.file_uploader("Seleccionar imagen del diagnóstico", type=["jpg", "png", "jpeg"])

    # Model selection
    model_type = st.selectbox("Seleccionar modelo", ["alexnet", "resnet"])
    view_type = st.selectbox("Seleccionar vista", ["saggital1", "axial", "saggital2"])

    if nombre_paciente and imagen_diagnostico:
        ruta_paciente = f"./Images/{nombre_paciente.replace(' ', '_')}"
        if os.path.exists(ruta_paciente):
            # Guardar imagen en el servidor
            fecha_actual = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
            ruta_imagen = f"{ruta_paciente}/{fecha_actual}.jpg"
            with open(ruta_imagen, "wb") as f:
                f.write(imagen_diagnostico.getbuffer())
            st.success(f"Imagen guardada en {ruta_imagen}")
            st.session_state["ultima_imagen"] = ruta_imagen

            # Realizar la predicción
            st.write("Realizando predicción con el modelo seleccionado...")
            # Predicción del modelo
            output = predict(ruta_imagen, model_type, view_type)

            # Mostrar los resultados
            st.write("Resultados de la predicción:")
            st.write(f"Predicción del modelo para {view_type}: {output}")
            
        else:
            st.error("Ha ingresado incorrectamente el nombre del paciente. Por favor, revise el nombre o regístrelo primero.")
    
    if st.button("Enviar a diagnóstico"):
        cambiar_pagina("resultados")

# Página de Resultados
def pagina_resultados():
    st.markdown("<div class='centered-title'>Resultados del Diagnóstico</div>", unsafe_allow_html=True)
    if "ultima_imagen" in st.session_state:
        ultima_imagen = st.session_state["ultima_imagen"]
        st.image(ultima_imagen, caption="Último diagnóstico cargado", use_column_width=True)
    else:
        st.warning("No hay una imagen cargada recientemente. Por favor, suba una imagen en la página de diagnóstico.")

# Página de Pacientes Registrados
def pagina_pacientes():
    st.markdown("<div class='centered-title'>Pacientes Registrados</div>", unsafe_allow_html=True)
    pacientes = os.listdir("./Images")
    
    if pacientes:
        for paciente in pacientes:
            st.markdown(f"""
            <div class="card">
                <a href="?page=historia_paciente&paciente={paciente}" target="_self">
                    <img src="https://img.icons8.com/ios-filled/50/000000/user.png" alt="Imagen de perfil">
                    <div class="container">
                        <h4><b>{paciente.replace('_', ' ')}</b></h4>
                    </div>
                </a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No hay pacientes registrados.")

# Página de Historia del Paciente
def historia_paciente(paciente):
    st.markdown(f"<div class='centered-title'>Historia de {paciente.replace('_', ' ')}</div>", unsafe_allow_html=True)
    imagenes = os.listdir(f"./Images/{paciente}")
    
    if imagenes:
        for imagen in imagenes:
            st.image(f"./Images/{paciente}/{imagen}", caption=imagen, use_column_width=True)
    else:
        st.warning("No hay imágenes para este paciente.")

# Navegación entre páginas
if st.session_state.page == "registrar_paciente":
    registrar_paciente()
elif st.session_state.page == "diagnostico_lumbar":
    diagnostico_lumbar()
elif st.session_state.page == "resultados":
    pagina_resultados()
elif st.session_state.page == "pacientes":
    pagina_pacientes()
elif st.session_state.page == "historia_paciente" and "paciente" in st.session_state:
    historia_paciente(st.session_state["paciente"])

# Navbar
# Columnas invisibles en la barra de navegación
col1, col2, col3 = st.columns(3)
# Botones con imágenes y enlaces a las funciones
with col1:
    if st.button("", key="registro"):
        cambiar_pagina("registrar_paciente")
    st.markdown("<button><img src='https://img.icons8.com/ios-filled/50/000000/paper.png' alt='Registro' title='Registro de Paciente'></button>", unsafe_allow_html=True)

with col2:
    if st.button("", key="diagnostico"):
        cambiar_pagina("diagnostico_lumbar")
    st.markdown("<button><img src='https://img.icons8.com/ios-filled/50/000000/treatment-plan.png' alt='Diagnóstico' title='Diagnóstico Lumbar'></button>", unsafe_allow_html=True)

with col3:
    if st.button("", key="pacientes"):
        cambiar_pagina("pacientes")
    st.markdown("<button><img src='https://img.icons8.com/ios-filled/50/000000/doctor-male.png' alt='Pacientes' title='Pacientes'></button>", unsafe_allow_html=True)

st.markdown("""
<div class="navbar">
    <a href="?page=registrar_paciente" target="_self">
        <img src="https://img.icons8.com/ios-filled/50/000000/paper.png" alt="Registro" title="Registro de Paciente">
    </a>
    <a href="?page=diagnostico_lumbar" target="_self">
        <img src="https://img.icons8.com/ios-filled/50/000000/treatment-plan.png" alt="Diagnóstico" title="Diagnóstico Lumbar">
    </a>
    <a href="?page=pacientes" >
        <img src="https://img.icons8.com/ios-filled/50/000000/doctor-male.png" alt="Pacientes" title="Pacientes">
    </a>
</div>
""", unsafe_allow_html=True)

# Manejo de parámetros en URL para navegación
query_params = st.query_params
if "page" in query_params:
    if query_params["page"][0] == "registrar_paciente":
        cambiar_pagina("registrar_paciente")
    elif query_params["page"][0] == "diagnostico_lumbar":
        cambiar_pagina("diagnostico_lumbar")
    elif query_params["page"][0] == "resultados":
        cambiar_pagina("resultados")
    elif query_params["page"][0] == "pacientes":
        cambiar_pagina("pacientes")
    elif query_params["page"][0] == "historia_paciente" and "paciente" in query_params:
        st.session_state["paciente"] = query_params["paciente"][0]
        cambiar_pagina("historia_paciente")
