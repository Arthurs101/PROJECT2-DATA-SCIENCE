import streamlit as st

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
            height: 60px;
            background-color: #f0f0f0;
            display: flex;
            justify-content: space-around;
            align-items: center;
        }
        .navbar img {
            width: 36px;
            height: 36px;
            cursor: pointer;
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
    </style>
""", unsafe_allow_html=True)

# Página de registro de paciente
if st.session_state.page == "registro_paciente":
    st.markdown("<div class='centered-title'>Agregar paciente</div>", unsafe_allow_html=True)
    st.markdown("<img src='https://images.vexels.com/media/users/3/200356/isolated/preview/127d177d9fda573481055d66bc602942-simbolo-del-caduceo-monocromo.png' class='centered-image'>", unsafe_allow_html=True)
    
    # Formulario de registro
    nombre = st.text_input("Nombre:", "", key="nombre", help="Ingrese el nombre del paciente", placeholder="Nombre del paciente")
    edad = st.text_input("Edad:", "", key="edad", help="Ingrese la edad del paciente", placeholder="Edad del paciente")
    imagen = st.file_uploader("Seleccionar imagen", type=["jpg", "png"], key="imagen")

    # Botón de agregar paciente
    if st.button("Agregar paciente", key="agregar_paciente"):
        st.success(f"Paciente {nombre} agregado con éxito.")

# Página de diagnóstico lumbar (principal)
elif st.session_state.page == "diagnostico_lumbar":
    st.markdown("<div class='centered-title'>Registro diagnóstico lumbar</div>", unsafe_allow_html=True)
    st.markdown("<img src='https://images.vexels.com/media/users/3/200356/isolated/preview/127d177d9fda573481055d66bc602942-simbolo-del-caduceo-monocromo.png' class='centered-image'>", unsafe_allow_html=True)

    # Formulario de diagnóstico
    num_paciente = st.text_input("No. Paciente:", "", key="num_paciente", help="Ingrese el número del paciente", placeholder="Número de paciente")
    nombre = st.text_input("Nombre:", "", key="nombre_diagnostico", help="Ingrese el nombre del paciente", placeholder="Nombre del paciente")
    imagen_diagnostico = st.file_uploader("Seleccionar imagen del diagnóstico", type=["jpg", "png"], key="imagen_diagnostico")

    # Botones en la página de diagnóstico
    if st.button("Enviar a diagnóstico", key="enviar_diagnostico"):
        st.success(f"Diagnóstico para el paciente {nombre} enviado con éxito.")
    
    if st.button("Ingresar Paciente", key="ingresar_paciente"):
        cambiar_pagina("registro_paciente")  # Cambiar a la página de registro de paciente

# Navbar con funcionalidad de cambio de página
st.markdown("""
    <div class="navbar">
        <a href="/?page=registro_paciente"><img src="https://img.icons8.com/ios-filled/50/000000/paper.png" title="Registro de Paciente"></a>
        <a href="/?page=diagnostico_lumbar"><img src="https://img.icons8.com/ios-filled/50/000000/treatment-plan.png" title="Diagnóstico Lumbar"></a>
        <img src="https://img.icons8.com/ios-filled/50/000000/doctor-male.png" title="Otros">
    </div>
""", unsafe_allow_html=True)

# Redirección en función de la página usando st.query_params
query_params = st.query_params
if query_params.get("page") == "registro_paciente":
    cambiar_pagina("registro_paciente")
elif query_params.get("page") == "diagnostico_lumbar":
    cambiar_pagina("diagnostico_lumbar")
