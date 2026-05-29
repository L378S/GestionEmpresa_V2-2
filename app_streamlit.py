import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

st.set_page_config(page_title="Sistema de Gestion Empresarial", layout="wide")

API_URL = "https://gestionempresa-v2-1.onrender.com/api"

if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None

def login():
    st.title("Sistema de Gestion Empresarial")
    st.subheader("Inicio de Sesion")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", use_container_width=True):
            try:
                response = requests.post(f"{API_URL}/login", params={
                    "username": username,
                    "password": password
                })
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.user = data["user"]
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
            except Exception as e:
                st.error(f"Error de conexion: {e}")

def main_app():
    st.sidebar.title("Menu Principal")
    st.sidebar.write(f"Usuario: {st.session_state.user['nombre_completo']}")
    st.sidebar.write(f"Rol: {st.session_state.user['rol']}")
    
    if st.sidebar.button("Cerrar Sesion"):
        st.session_state.token = None
        st.session_state.user = None
        st.rerun()
    
    menu = st.sidebar.selectbox("Modulo", [
        "Dashboard",
        "Ingresos",
        "Materiales",
        "Pagos Trabajadores",
        "Deudas"
    ])
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    if menu == "Dashboard":
        st.header("Tablero de Control")
        semana = st.selectbox("Semana", list(range(1, 53)), format_func=lambda x: f"Semana {x}")
        
        try:
            response = requests.get(f"{API_URL}/dashboard", params={"semana": semana}, headers=headers)
            if response.status_code == 200:
                data = response.json()
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Ingresos Totales", f"$ {data['total_ingresos']:,.2f}")
                col2.metric("Egresos Totales", f"$ {data['total_egresos']:,.2f}")
                col3.metric("Utilidad", f"$ {data['utilidad']:,.2f}")
                col4.metric("Numero Ingresos", data['num_ingresos'])
        except Exception as e:
            st.error(f"Error: {e}")
    
    elif menu == "Ingresos":
        st.header("Registro de Ingresos")
        with st.form("form_ingreso"):
            fecha = st.date_input("Fecha", datetime.now())
            cliente = st.text_input("Cliente")
            concepto = st.text_input("Concepto")
            monto = st.number_input("Monto", min_value=0.01, step=0.01)
            categoria = st.selectbox("Categoria", ["Servicios", "Productos", "Consultorias", "Otros"])
            referencia = st.text_input("Referencia")
            
            if st.form_submit_button("Registrar Ingreso"):
                try:
                    response = requests.post(f"{API_URL}/ingresos", params={
                        "cliente": cliente, "concepto": concepto, "monto": monto,
                        "categoria": categoria, "fecha": fecha.isoformat(), "referencia": referencia
                    }, headers=headers)
                    if response.status_code == 200:
                        st.success("Ingreso registrado")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    elif menu == "Materiales":
        st.header("Registro de Materiales")
        with st.form("form_material"):
            nombre = st.text_input("Nombre")
            cantidad = st.number_input("Cantidad", min_value=1)
            costo_unitario = st.number_input("Costo Unitario", min_value=0.01)
            proveedor = st.text_input("Proveedor")
            fecha = st.date_input("Fecha", datetime.now())
            
            if st.form_submit_button("Registrar Material"):
                try:
                    response = requests.post(f"{API_URL}/materiales", params={
                        "nombre": nombre, "cantidad": cantidad, "costo_unitario": costo_unitario,
                        "proveedor": proveedor, "fecha": fecha.isoformat()
                    }, headers=headers)
                    if response.status_code == 200:
                        st.success("Material registrado")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    elif menu == "Pagos Trabajadores":
        st.header("Pagos a Trabajadores")
        with st.form("form_pago"):
            nombre = st.text_input("Nombre")
            dias_trabajados = st.number_input("Dias", min_value=0, max_value=7)
            pago_diario = st.number_input("Pago por Dia", min_value=0.01)
            fecha_pago = st.date_input("Fecha Pago", datetime.now())
            
            if st.form_submit_button("Registrar Pago"):
                try:
                    response = requests.post(f"{API_URL}/empleados", params={
                        "nombre": nombre, "dias_trabajados": dias_trabajados,
                        "pago_diario": pago_diario, "fecha_pago": fecha_pago.isoformat()
                    }, headers=headers)
                    if response.status_code == 200:
                        st.success("Pago registrado")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    elif menu == "Deudas":
        st.header("Registro de Deudas")
        with st.form("form_deuda"):
            acreedor = st.text_input("Acreedor")
            monto = st.number_input("Monto", min_value=0.01)
            fecha_vencimiento = st.date_input("Fecha Vencimiento", datetime.now())
            nota = st.text_area("Nota")
            
            if st.form_submit_button("Registrar Deuda"):
                try:
                    response = requests.post(f"{API_URL}/deudas", params={
                        "acreedor": acreedor, "monto": monto,
                        "fecha_vencimiento": fecha_vencimiento.isoformat(), "nota": nota
                    }, headers=headers)
                    if response.status_code == 200:
                        st.success("Deuda registrada")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

if st.session_state.token is None:
    login()
else:
    main_app()