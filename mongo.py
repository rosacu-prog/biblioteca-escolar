import time
from narwhals import col
import pandas as pd
import streamlit as st
from bson.objectid import ObjectId
from pymongo import MongoClient

st.set_page_config(page_title="Biblioteca Angli Lara", layout="wide")

st.markdown("""
    <style>
        
            
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }
            
        .st-emotion-cache-1wbqy5l{
            visibility: hidden !important;
        }

    </style>
""", unsafe_allow_html=True)


# Establece la conexión con MongoDB, usando la URI de conexión proporcionada por MongoDB Atlas (o tu servidor local)
conexion_mongodb = MongoClient(st.secrets["URI"])

# Llama a la base de datos
base_datos = conexion_mongodb["BIBLIOTECA"]

# De la base de datos, llama las colecciones
coleccion_libros = base_datos["LIBROS"]
coleccion_usuarios = base_datos["USUARIOS"]
coleccion_prestamos = base_datos["PRESTAMOS"]

# Creamos el sidebar y asignamos el logo y el Título
st.sidebar.image("logos/logo_angli.jpg", width=100)
st.sidebar.title("Biblioteca Fernando E. Angli Lara")
# sidebar menú lateral para navegar entre ventanas
modulo_seleccionado = st.sidebar.radio(
    "Selecciona un área:", 
    ["Libros", "Usuarios", "Préstamos"]
)

# Se elimina el texto buscado y limpia el contenedor para una nueva búsqueda    
if "reset_input" not in st.session_state:
    st.session_state.reset_input = 0

# MÓDULO 1: LIBROS
if modulo_seleccionado == "Libros":
    st.header("Gestión de Libros")
    
    # Obtener datos, extrae los documents de mongo y los convierte a una lista (organización de datos)
    datos_libros = list(coleccion_libros.find({"eliminado": {"$ne": True}})) # Solo trae los libros que no tienen eliminado: true, o sea los que no han sido eliminados (si el campo eliminado no existe, también lo trae)

    #Validación del contenido de la bdd, si esta vacía arroja un mensaje de error
    if not datos_libros:
        st.warning("La base de datos está vacía.")
        st.stop()

    # Convertir a DataFrame (o sea como una tabla de excel y muestra todas las claves de esa coleccion en formato tabla)
    coleccion_tabla_libros = pd.DataFrame(datos_libros)
    
    tab_buscar_libros, tab_crear_libro, tab_editar_libros, tab_eliminar_libros = st.tabs(["🔍 Buscar Libro", "➕ Agregar Libro", "✏️ Editar", "❌ Eliminar"])
    
    #Inicia bloque de búsqueda de libros
    with tab_buscar_libros:
        st.subheader("Buscador de la Biblioteca")

        if "_id" in coleccion_tabla_libros.columns and 'eliminado' in coleccion_tabla_libros.columns:
            coleccion_tabla_libros = coleccion_tabla_libros.drop(columns=["_id"])
            coleccion_tabla_libros = coleccion_tabla_libros.drop(columns=["eliminado"])

        # Buscador
        input_nombre = st.text_input("Buscar libro", help="Busca por Título, Editorial, Autor o Categoria") # Se le agrega un helper (texto de ayuda) para que se vea bonito

        list_columnas = [
            'Título',
            'Editorial',
            'Autor',
            'Categoría'
        ]

        # coleccion_tabla_libros.columns son todas las columnas(claves) de la coleccion de libros
        # col = Título, Editorial, autor, categoria, fecha, ect.......
        #Extrae las claves de mi colección y las agrupa en la variable "col", para posteriormente hacer un ciclo (búsqueda) hasta que coincida con alguna de las opciones a buscar
        if all(col in coleccion_tabla_libros.columns for col in list_columnas):

            #Conversión de tipo de dato a string para evitar errores de coincidencia de datos
            if "Cantidad" in coleccion_tabla_libros.columns:
                coleccion_tabla_libros["Cantidad"] = pd.to_numeric(coleccion_tabla_libros["Cantidad"], errors="coerce")
                # Rellena cualquier vacío con 0 y convierte toda la columna a número entero (int)
                coleccion_tabla_libros["Cantidad"] = coleccion_tabla_libros["Cantidad"].fillna(0).astype(int)

            list_columnas_texto = ["Título", "Editorial", "Autor", "Categoría", "Edición", "Fecha de publicación"] # Lista de columnas que se espera que sean de texto

            for col in list_columnas_texto:
                if col in coleccion_tabla_libros.columns:
                    coleccion_tabla_libros[col] = coleccion_tabla_libros[col].fillna("N/A")

            #verifica si realmente el usuario escribió algo
            if input_nombre:  
                # 1. Opciones para filtrar por el input ingresado, validando el texto ingresado por el usuario (si esta bien escrito, una palabra coincidente, convierte lo escrito en el buscador a string y evita errores que rompan el sistema)
                filtro_Título = coleccion_tabla_libros["Título"].astype(str).str.contains(input_nombre, case=False, na=False)
                filtro_editorial = coleccion_tabla_libros["Editorial"].astype(str).str.contains(input_nombre, case=False, na=False)
                filtro_autor = coleccion_tabla_libros["Autor"].astype(str).str.contains(input_nombre, case=False, na=False)
                filtro_categoria = coleccion_tabla_libros["Categoría"].astype(str).str.contains(input_nombre, case=False, na=False)
                
                # Aplicamos filtros con el operador OR (|) para que mi instrucción se cumpla siempre y cuando alguna de las columnas sea coincidente
                resultados = coleccion_tabla_libros[filtro_Título | filtro_editorial | filtro_autor | filtro_categoria]
                
                # Mostramos la tabla si hay resultados (si resultados no esta vacío)
                if not resultados.empty:
                    st.dataframe(resultados)
                else:
                    st.info(f"No se encontró resultados para la búsqueda: {input_nombre}")
                    
            else:
                # Si la barra de búsqueda está vacía, mostramos toda la tabla por defecto
                st.dataframe(coleccion_tabla_libros)    
        else:
            st.error("Error: No se encontro columnas en la base de datos.")
    
    #Inicia bloque de creación de libros
    with tab_crear_libro:
        st.subheader("Agregar un nuevo libro")
    
        # Creamos un formulario para ingresar la info de un nuevo libro
        with st.form("form_nuevo_libro", enter_to_submit=False):
            col1, col2 = st.columns(2)

            #Organiza el formulario en dos columnas 
            with col1:
                nuevo_titulo = st.text_input("Título del libro", key=f"Título_{st.session_state.reset_input}")
                nuevo_editorial = st.text_input("Editorial", key=f"editorial_{st.session_state.reset_input}")
                nuevo_autor = st.text_input("Autor", key=f"autor_{st.session_state.reset_input}")
                nuevo_edicion = st.text_input("Edición", key=f"edicion_{st.session_state.reset_input}")
            with col2:
                nuevo_anio = st.text_input("Fecha de publicación", key=f"fecha_publicacion_{st.session_state.reset_input}")
                nuevo_cantidad = st.number_input("Cantidad", value=0, step=1, key=f"cantidad_{st.session_state.reset_input}")
                nuevo_categoria = st.text_input("Categoría", key=f"categoria_{st.session_state.reset_input}")
            
            btn_guardar = st.form_submit_button("Guardar en base de datos")
            
            #Al clickear el btn guardar, se inicia la conexión e insersión en la colección libros de la base de datos
            if btn_guardar:
                if nuevo_titulo and nuevo_autor and nuevo_editorial: # Validación para campos obligatorios del formulario de regristro de un nuevo libro
                    nuevo_documento = {
                        "Título": nuevo_titulo,
                        "Autor": nuevo_autor,
                        "Editorial": nuevo_editorial,
                        "Cantidad": nuevo_cantidad if nuevo_cantidad else None, #Valida si el campo queda vacío, ingrese un valor none a la clave en la bdd
                        "Fecha de publicación":nuevo_anio if nuevo_anio else None,
                        "Categoría":nuevo_categoria if nuevo_categoria else None,
                        "Edición":nuevo_edicion if nuevo_edicion else None,
                        "eliminado": False
                    }

                    coleccion_libros.insert_one(nuevo_documento) # Inserta los datos a la base de datos
                    st.success(f"¡El libro '{nuevo_titulo}' se agregó correctamente!")
                    st.session_state.reset_input += 1
                    time.sleep(2)
                    st.rerun() # Recarga la app para que la tabla principal se actualice
                else:
                    st.warning("Por favor, llena todos los campos.")

    #Inicia bloque de edición de libros    
    with tab_editar_libros:
        st.subheader("Editar un libro existente")

        if not coleccion_tabla_libros.empty:
            lista_libros = coleccion_tabla_libros["Título"].tolist()
            
            libro_seleccionado = st.selectbox("Selecciona el libro a editar:", lista_libros)
            
            # Extraemos los datos del libro
            datos_libro = coleccion_tabla_libros[coleccion_tabla_libros["Título"] == libro_seleccionado].iloc[0]
            
            # Extraemos las copias actuales (usamos .get() por si tienes libros viejos sin ese campo)
            # y lo convertimos a int para el number_input
            valor_copias = datos_libro.get("Cantidad", 0)
        
            if pd.isna(valor_copias):
                copias_actuales = 0
            else:
                copias_actuales = int(valor_copias)
            
            with st.form("form_editar_libro"):
                col1, col2 = st.columns(2)

                with col1:
                    edit_titulo = st.text_input("Título", value=datos_libro["Título"], key=f"titulo_{st.session_state.reset_input}_{libro_seleccionado}")
                    edit_editorial = st.text_input("Editorial", value=datos_libro["Editorial"], key=f"editorial_{st.session_state.reset_input}_{libro_seleccionado}")
                    edit_autor = st.text_input("Autor", value=datos_libro["Autor"], key=f"autor_{st.session_state.reset_input}_{libro_seleccionado}")
                with col2:
                    edit_cantidad = st.number_input("Cantidad de copias", min_value=0, step=1, value=copias_actuales, key=f"cantidad_{st.session_state.reset_input}_{libro_seleccionado}")
                    edit_categoria = st.text_input("Categoría", value=datos_libro["Categoría"], key=f"categoria_{st.session_state.reset_input}_{libro_seleccionado}")
                    edit_edicion = st.text_input("Edición", value=datos_libro["Edición"], key=f"edicion_{st.session_state.reset_input}_{libro_seleccionado}")

                
                btn_actualizar = st.form_submit_button("Actualizar libro")
                
                if btn_actualizar:
                    if edit_titulo and edit_autor and edit_categoria:
                        # Buscamos por el título original, y sobreescribimos con los datos nuevos
                        coleccion_libros.update_one(
                            {"Título": libro_seleccionado}, 
                            {"$set": {                      
                                "Título": edit_titulo,
                                "Editorial": edit_editorial,
                                "Autor": edit_autor,
                                "Cantidad": edit_cantidad,
                                "Categoría": edit_categoria,
                                "Edición": edit_edicion
                            }}
                        )
                        
                        st.success(f"¡El libro '{libro_seleccionado}' fue actualizado con éxito!")
                        st.session_state.reset_input += 1
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.warning("Los campos de texto (Título, Autor, Género) no pueden estar vacíos.")
        else:
            st.info("No hay libros registrados para poder editar.")

    #Inicia bloque de eliminación de libros
    with tab_eliminar_libros:
        st.subheader("Eliminar un libro del registro")
    
        if not coleccion_tabla_libros.empty:
            # Obtenemos una lista de todos los títulos para el menú desplegable
            lista_titulos = coleccion_tabla_libros["Título"].tolist() 
            
            libro_a_eliminar = st.selectbox("Selecciona el libro a eliminar:", lista_titulos)
            
            if st.button("Eliminar permanentemente", type="primary"):
                # Le decimos a MongoDB que borre el documento con ese título
                coleccion_libros.update_one({"Título": libro_a_eliminar}, {"$set": {"eliminado": True}})
                st.success(f"¡El libro '{libro_a_eliminar}' ha sido eliminado!")
                time.sleep(2)
                st.rerun() # Actualiza la pantalla
        else:
            st.info("No hay libros para eliminar.")
    # with tab_eliminar_libros:
    #     st.subheader("Eliminar un libro del registro")
    
    #     if not coleccion_tabla_libros.empty:
    #         # Obtenemos una lista de todos los títulos para el menú desplegable
    #         lista_titulos = coleccion_tabla_libros["Título"].tolist() 
            
    #         libro_a_eliminar = st.selectbox("Selecciona el libro a eliminar:", lista_titulos)
            
    #         if st.button("Eliminar permanentemente", type="primary"):
    #             # Le decimos a MongoDB que borre el documento con ese título
    #             coleccion_libros.delete_one({"Título": libro_a_eliminar})
    #             st.success(f"¡El libro '{libro_a_eliminar}' ha sido eliminado!")
    #             time.sleep(2)
    #             st.rerun() # Actualiza la pantalla
    #     else:
    #         st.info("No hay libros para eliminar.")

# MÓDULO 2: USUARIOS
elif modulo_seleccionado == "Usuarios":
    st.header("Gestión de Alumnos y Lectores")

    datos_usuarios = list(coleccion_usuarios.find())

    if not datos_usuarios:
        st.warning("La base de datos está vacía.")
        st.stop()

    df_usuarios = pd.DataFrame(datos_usuarios)

    if not datos_usuarios:
            st.warning("La base de datos está vacía.")
            st.stop()
    
    tab_lista_usuarios, tab_nuevo_usuario, tab_editar_usuario, tab_eliminar_usuario = st.tabs(["📋 Lista", "➕ Registrar", "✏️ Editar", "❌ Eliminar"])
    
    with tab_lista_usuarios:
        st.subheader("Lista de usuarios")

        if not df_usuarios.empty:
            df_mostrar = df_usuarios.copy()
            
            # 1. UNIFICAR NOMBRES Y APELLIDOS
            if 'Nombres' in df_mostrar.columns and 'Nombre' in df_mostrar.columns:
                df_mostrar['Nombres'] = df_mostrar['Nombres'].combine_first(df_mostrar['Nombre'])
            elif 'Nombre' in df_mostrar.columns:
                df_mostrar['Nombres'] = df_mostrar['Nombre']
                
            if 'Apellidos' in df_mostrar.columns and 'Apellido' in df_mostrar.columns:
                df_mostrar['Apellidos'] = df_mostrar['Apellidos'].combine_first(df_mostrar['Apellido'])
            elif 'Apellido' in df_mostrar.columns:
                df_mostrar['Apellidos'] = df_mostrar['Apellido']

            # 2. UNIFICAR OCUPACIÓN / TIPO
            if 'ocupacion' in df_mostrar.columns and 'Tipo' in df_mostrar.columns:
                df_mostrar['Ocupación'] = df_mostrar['ocupacion'].combine_first(df_mostrar['Tipo'])
            elif 'ocupacion' in df_mostrar.columns:
                df_mostrar['Ocupación'] = df_mostrar['ocupacion']
            elif 'Tipo' in df_mostrar.columns:
                df_mostrar['Ocupación'] = df_mostrar['Tipo']

            # 3. ELIMINAR COLUMNAS REDUNDANTES Y BASURA
            # Borramos las columnas en singular y el _id porque ya unificamos la información
            columnas_basura = ["_id", "Nombre", "Apellido", "ocupacion", "Tipo"]
            columnas_a_borrar = [col for col in columnas_basura if col in df_mostrar.columns]
            df_mostrar = df_mostrar.drop(columns=columnas_a_borrar)

            # 4. LIMPIAR LOS "NONE" RESTANTES
            # Rellenamos los huecos (por ejemplo, los alumnos que no tienen 'Materia') con 'N/A'
            df_mostrar = df_mostrar.fillna("N/A")

            # 5. REORDENAR COLUMNAS (Opcional, para que se vea más organizado)
            # Extraemos las columnas principales al inicio y dejamos el resto al final
            columnas_principales = ["Nombres", "Apellidos", "Ocupación", "Correo"]
            columnas_existentes = [col for col in columnas_principales if col in df_mostrar.columns]
            columnas_extra = [col for col in df_mostrar.columns if col not in columnas_existentes]
            
            df_mostrar = df_mostrar[columnas_existentes + columnas_extra]

            # Mostramos la tabla limpia
            st.dataframe(df_mostrar, use_container_width=True)
        else:
            st.info("No hay usuarios registrados.")

    with tab_nuevo_usuario:
        st.subheader("Agregar un nuevo usuario")

        # 1. EL SELECTBOX VA AFUERA DEL FORMULARIO
        # Usamos directamente los valores de tu BD ('alumno', 'docente', 'externo')
        n_ocupacion = st.selectbox(
            "Selecciona el tipo de usuario a registrar:", 
            ["alumno", "docente", "externo"], 
            key=f"Tipo_usuario_{st.session_state.reset_input}"
        )

        # 2. CREAMOS EL FORMULARIO
        with st.form("form_nuevo_usuario"):
            col1, col2 = st.columns(2)
            
            with col1:
                n_nombre = st.text_input("Nombre(s)", key=f"Nombre_usuario_{st.session_state.reset_input}")
                n_apellido = st.text_input("Apellido(s)", key=f"Apellido_usuario_{st.session_state.reset_input}")
                n_correo = st.text_input("Correo electrónico", key=f"Correo_usuario_{st.session_state.reset_input}")
                n_turno = st.selectbox("Turno", ["Matutino", "Vespertino", "N/A"], key=f"Turno_{st.session_state.reset_input}")

            with col2:
                # 3. IF DINÁMICO PARA MOSTRAR INPUTS SEGÚN LA OCUPACIÓN
                if n_ocupacion == "alumno":
                    n_grado = st.text_input("Grado", key=f"Grado_usuario_{st.session_state.reset_input}")
                    n_grupo = st.text_input("Grupo", key=f"Grupo_usuario_{st.session_state.reset_input}")
                    n_especialidad = st.text_input("Especialidad", key=f"Especialidad_{st.session_state.reset_input}")
                
                elif n_ocupacion == "docente":
                    n_materia = st.text_input("Materia", key=f"Materia_{st.session_state.reset_input}")
                    n_carrera = st.text_input("Carrera", key=f"Carrera_{st.session_state.reset_input}")
                
                elif n_ocupacion == "externo":
                    st.info("No se requieren campos adicionales para personal externo.")

            # 4. BOTÓN DE ENVÍO Y GUARDADO EN MONGO
            if st.form_submit_button("Registrar Usuario"):
                if n_nombre and n_apellido:
                    
                    # Creamos el diccionario base con los datos generales
                    nuevo_user = {
                        "Nombres": n_nombre,
                        "Apellidos": n_apellido,
                        "Correo": n_correo,
                        "Turno": n_turno,
                        "ocupacion": n_ocupacion
                    }

                    # Agregamos las claves específicas al diccionario dependiendo de la ocupación
                    if n_ocupacion == "alumno":
                        nuevo_user["Grado"] = n_grado
                        nuevo_user["Grupo"] = n_grupo
                        nuevo_user["Especialidad"] = n_especialidad
                        
                    elif n_ocupacion == "docente":
                        nuevo_user["Materia"] = n_materia
                        nuevo_user["Carrera"] = n_carrera

                    # Insertamos en la base de datos
                    coleccion_usuarios.insert_one(nuevo_user)
                    st.success(f"¡Usuario {n_nombre} registrado correctamente como {n_ocupacion}!")
                    
                    st.session_state.reset_input += 1
                    time.sleep(2)
                    st.rerun()
                else:
                    st.warning("El Nombre y Apellido son obligatorios para poder registrar.")
    
    with tab_editar_usuario:
        st.subheader("Editar un usuario")

        if not df_usuarios.empty:
            nombres_completos = [f"{u.get('Nombres', u.get('Nombre', ''))} {u.get('Apellidos', u.get('Apellido', ''))} - ({u.get('ocupacion', 'N/A')})".strip() for u in datos_usuarios]
            user_seleccionado = st.selectbox("Selecciona usuario a editar:", nombres_completos)
            
            # Buscamos los datos originales del usuario seleccionado
            datos_u = datos_usuarios[nombres_completos.index(user_seleccionado)]
            
            # 1. CALCULAMOS QUÉ OCUPACIÓN TIENE ACTUALMENTE PARA PRE-SELECCIONARLA
            opciones_ocupacion = ["alumno", "docente", "externo"]
            ocupacion_actual = datos_u.get("ocupacion", "alumno").lower() # Por si se guardó en mayúsculas por error
            
            if ocupacion_actual in opciones_ocupacion:
                index_ocupacion = opciones_ocupacion.index(ocupacion_actual)
            else:
                index_ocupacion = 0 # Selecciona 'alumno' por defecto si algo falla

            # 2. SELECTBOX DE OCUPACIÓN AFUERA DEL FORMULARIO
            e_ocupacion = st.selectbox(
                "Ocupación", 
                opciones_ocupacion, 
                index=index_ocupacion, 
                key=f"edit_ocupacion_{st.session_state.reset_input}_{datos_u['_id']}"
            )
            
            # 3. CREAMOS EL FORMULARIO
            with st.form("form_editar_usuario"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Datos generales (para todos)
                    e_nombre = st.text_input("Nombre", value=datos_u.get("Nombres", datos_u.get("Nombre", "")), key=f"edit_Nombre_{st.session_state.reset_input}")
                    e_apellido = st.text_input("Apellido", value=datos_u.get("Apellidos", datos_u.get("Apellido", "")), key=f"edit_Apellido_{st.session_state.reset_input}")
                    e_correo = st.text_input("Correo", value=datos_u.get("Correo", ""), key=f"edit_Correo_{st.session_state.reset_input}")
                    
                    # Para el Turno, también calculamos su índice para pre-seleccionarlo
                    opciones_turno = ["Matutino", "Vespertino", "N/A"]
                    turno_actual = datos_u.get("Turno", "N/A")
                    index_turno = opciones_turno.index(turno_actual) if turno_actual in opciones_turno else 2
                    e_turno = st.selectbox("Turno", opciones_turno, index=index_turno, key=f"edit_Turno_{st.session_state.reset_input}")

                with col2:
                    # 4. IF DINÁMICO PARA MOSTRAR INPUTS SEGÚN LA OCUPACIÓN SELECCIONADA
                    if e_ocupacion == "alumno":
                        e_grado = st.text_input("Grado", value=datos_u.get("Grado", ""), key=f"edit_Grado_{st.session_state.reset_input}")
                        e_grupo = st.text_input("Grupo", value=datos_u.get("Grupo", ""), key=f"edit_Grupo_{st.session_state.reset_input}")
                        e_especialidad = st.text_input("Especialidad", value=datos_u.get("Especialidad", ""), key=f"edit_Especialidad_{st.session_state.reset_input}")
                    
                    elif e_ocupacion == "docente":
                        e_materia = st.text_input("Materia / Prefectura", value=datos_u.get("Materia", ""), key=f"edit_Materia_{st.session_state.reset_input}")
                        e_carrera = st.text_input("Carrera", value=datos_u.get("Carrera", ""), key=f"edit_Carrera_{st.session_state.reset_input}")
                    
                    elif e_ocupacion == "externo":
                        st.info("No hay campos adicionales para editar en personal externo.")

                # 5. ACTUALIZACIÓN EN BASE DE DATOS
                if st.form_submit_button("Actualizar"):
                    if e_nombre and e_apellido:
                        
                        # Armamos el diccionario base con los datos generales
                        datos_actualizados = {
                            "Nombres": e_nombre, 
                            "Apellidos": e_apellido,
                            "Correo": e_correo,
                            "Turno": e_turno,
                            "ocupacion": e_ocupacion
                        }

                        # Agregamos los campos específicos dependiendo de lo que se seleccionó
                        if e_ocupacion == "alumno":
                            datos_actualizados["Grado"] = e_grado
                            datos_actualizados["Grupo"] = e_grupo
                            datos_actualizados["Especialidad"] = e_especialidad
                        elif e_ocupacion == "docente":
                            datos_actualizados["Materia"] = e_materia
                            datos_actualizados["Carrera"] = e_carrera

                        # Actualizamos en MongoDB
                        coleccion_usuarios.update_one(
                            {"_id": datos_u["_id"]},
                            {"$set": datos_actualizados}
                        )
                        
                        st.success("¡Usuario actualizado correctamente!")
                        st.session_state.reset_input += 1
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.warning("El Nombre y Apellido no pueden quedar vacíos.")
        else:
            st.info("No hay usuarios registrados para poder editar.")

    with tab_eliminar_usuario:
        st.subheader("Eliminar un usuario")

        if not df_usuarios.empty:
            nombres_completos = [f"{u.get('Nombres', u.get('Nombre', ''))} {u.get('Apellidos', u.get('Apellido', ''))} - ({u.get('ocupacion', 'N/A')})".strip() for u in datos_usuarios]

            user_a_eliminar = st.selectbox("Selecciona usuario a eliminar:", nombres_completos, key="del_user")
            datos_del = df_usuarios.iloc[nombres_completos.index(user_a_eliminar)]
            
            if st.button("Eliminar permanentemente", type="primary"):
                coleccion_usuarios.delete_one({"_id": datos_del["_id"]})
                st.success("Usuario eliminado.")
                time.sleep(2)
                st.rerun()

# MÓDULO 3: PRÉSTAMOS
elif modulo_seleccionado == "Préstamos":
    st.header("Préstamos y Devoluciones")
    
    # Extraemos todos los datos necesarios
    datos_libros = list(coleccion_libros.find())
    datos_usuarios = list(coleccion_usuarios.find())
    datos_prestamos = list(coleccion_prestamos.find())
    
    tab_activos, tab_prestar, tab_devolver = st.tabs(["⏱️ Préstamos Activos", "📤 Prestar Libro", "📥 Recibir Devolución"])
    
    # --- LEER PRÉSTAMOS ACTIVOS ---
    with tab_activos:
        df_prestamos = pd.DataFrame(datos_prestamos)

        if not df_prestamos.empty:
            # CORRECCIÓN 1 y 2: 'devuelto' en minúscula y comparado con el booleano False
            df_activos = df_prestamos[df_prestamos["devuelto"] == False].copy()
            
            if not df_activos.empty:
                # CORRECCIÓN 3: Creamos diccionarios traductores validando alumnos (Nombres) y docentes (Nombre)
                map_usuarios = {}
                for u in datos_usuarios:
                    nombre = u.get("Nombres", u.get("Nombre", "Usuario"))
                    apellido = u.get("Apellidos", u.get("Apellido", ""))
                    ocupacion = u.get("ocupacion", "N/A")
                    map_usuarios[str(u['_id'])] = f"{nombre} {apellido} - ({ocupacion})".strip()
                
                map_libros = {str(l['_id']): l.get('Título', 'Libro Desconocido') for l in datos_libros}
                
                # Creamos nuevas columnas más bonitas usando los traductores
                df_activos["Usuario"] = df_activos["usuario_id"].astype(str).map(map_usuarios)
                df_activos["Libro"] = df_activos["libro_id"].astype(str).map(map_libros)
                
                # Limpiamos la tabla eliminando las columnas de IDs
                columnas_basura = ["_id", "usuario_id", "libro_id", "devuelto"]
                columnas_a_borrar = [col for col in columnas_basura if col in df_activos.columns]
                df_activos = df_activos.drop(columns=columnas_a_borrar)
                
                # Reordenamos y renombramos las columnas (fecha_prestamo en bd no lleva acento)
                df_activos = df_activos[["Usuario", "Libro", "fecha_prestamo", "fecha_devolucion"]]
                df_activos = df_activos.rename(columns={
                    "fecha_prestamo": "Fecha de Préstamo",
                    "fecha_devolucion": "Fecha de Devolución"
                })
                
                st.dataframe(df_activos, use_container_width=True)
            else:
                st.info("No hay préstamos activos en este momento.")
        else:
            st.info("No hay registros de préstamos en el sistema.")

    # --- PRESTAR LIBRO (Insertar) ---
    with tab_prestar:
        if not datos_libros or not datos_usuarios:
            st.warning("Necesitas registrar al menos un libro y un usuario primero.")
        else:
            with st.form("form_nuevo_prestamo"):
                
                dict_usuarios = {}
                for u in datos_usuarios:
                    nombre = u.get("Nombres", u.get("Nombre", "Usuario"))
                    apellido = u.get("Apellidos", u.get("Apellido", ""))
                    ocupacion = u.get("ocupacion", "N/A")
                    nombre_completo = f"{nombre} {apellido} - ({ocupacion})".strip()
                    dict_usuarios[nombre_completo] = str(u["_id"])
                
                dict_libros = {}
                for l in datos_libros:
                    cantidad_str = l.get("Cantidad", 0)
                    cantidad = int(cantidad_str) if str(cantidad_str).strip() != "" else 0
                    
                    if cantidad > 0:
                        titulo = l.get("Título", "Libro sin título")
                        dict_libros[titulo] = str(l["_id"])

                if not dict_libros:
                    st.error("No hay libros disponibles con cantidad en inventario.")
                else:
                    sel_usuario = st.selectbox("Selecciona al Usuario:", list(dict_usuarios.keys()), key=f"Usuario_prestamo_{st.session_state.reset_input}")
                    sel_libro = st.selectbox("Selecciona el Libro:", list(dict_libros.keys()), key=f"Libro_prestamo_{st.session_state.reset_input}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        fecha_p = st.date_input("Fecha de Préstamo", key=f"FechaP_prestamo_{st.session_state.reset_input}")
                    with col2:
                        fecha_d = st.date_input("Fecha de Devolución", key=f"FechaD_prestamo_{st.session_state.reset_input}")
                    
                    if st.form_submit_button("Registrar Préstamo"):
                        id_usuario_str = dict_usuarios[sel_usuario]
                        id_libro_str = dict_libros[sel_libro]
                        
                        nuevo_prestamo = {
                            "usuario_id": ObjectId(id_usuario_str), 
                            "libro_id": ObjectId(id_libro_str),
                            "fecha_prestamo": str(fecha_p),
                            "fecha_devolucion": str(fecha_d),
                            "devuelto": False
                        }
                        coleccion_prestamos.insert_one(nuevo_prestamo)
                        
                        libro_actual_data = next((l for l in datos_libros if str(l['_id']) == id_libro_str), {})
                        cantidad_actual = int(libro_actual_data.get("Cantidad", 0))
                        
                        coleccion_libros.update_one(
                            {"_id": ObjectId(id_libro_str)}, 
                            {"$set": {"Cantidad": cantidad_actual - 1}} 
                        )
                        
                        st.success("Préstamo registrado exitosamente.")
                        st.session_state.reset_input += 1
                        time.sleep(2)
                        st.rerun()

    # --- RECIBIR DEVOLUCIÓN (Actualizar) ---
    with tab_devolver:
        # CORRECCIÓN 1: Buscar el booleano False directo
        prestamos_activos = list(coleccion_prestamos.find({"devuelto": False}))
        
        if prestamos_activos:
            # CORRECCIÓN 3: Unificamos búsqueda de nombres de alumnos y docentes
            map_usuarios = {}
            for u in datos_usuarios:
                nombre = u.get("Nombres", u.get("Nombre", "Usuario"))
                apellido = u.get("Apellidos", u.get("Apellido", ""))
                ocupacion = u.get("ocupacion", "N/A")
                map_usuarios[str(u['_id'])] = f"{nombre} {apellido} - ({ocupacion})".strip()
                
            map_libros = {str(l['_id']): l.get('Título', 'Libro Desconocido') for l in datos_libros}
            
            with st.form("form_devolucion"):
                opciones_prestamos = []
                for p in prestamos_activos:
                    nombre_u = map_usuarios.get(str(p['usuario_id']), "Usuario Desconocido")
                    titulo_l = map_libros.get(str(p['libro_id']), "Libro Desconocido")
                    
                    texto = f"Libro:  {titulo_l}  -  Prestado a:  {nombre_u} | Fecha: {p.get('fecha_prestamo')}"
                    opciones_prestamos.append(texto)
                
                prestamo_seleccionado = st.selectbox("Selecciona el préstamo a marcar como devuelto:", opciones_prestamos, key=f"Prestamo_{st.session_state.reset_input}")
                
                if st.form_submit_button("Confirmar Devolución"):
                    idx = opciones_prestamos.index(prestamo_seleccionado)
                    datos_p = prestamos_activos[idx]
                    
                    # CORRECCIÓN 1: Establecer como booleano True
                    coleccion_prestamos.update_one(
                        {"_id": datos_p["_id"]},
                        {"$set": {"devuelto": True}}
                    )
                    
                    libro_a_devolver = coleccion_libros.find_one({"_id": ObjectId(datos_p["libro_id"])})
                    
                    # CORRECCIÓN 4: Leer la "Cantidad" en lugar de "Copias"
                    cantidad_actual = int(libro_a_devolver.get("Cantidad", 0)) if libro_a_devolver else 0
                    
                    # Sumamos 1 y sobrescribimos "Cantidad"
                    coleccion_libros.update_one(
                        {"_id": ObjectId(datos_p["libro_id"])},
                        {"$set": {"Cantidad": cantidad_actual + 1}}
                    )
                    
                    st.success("¡Libro devuelto al inventario con éxito!")
                    st.session_state.reset_input += 1
                    time.sleep(2)
                    st.rerun()
        else:
            st.info("Todos los libros han sido devueltos. ¡Excelente!")