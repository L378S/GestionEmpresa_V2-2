from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import json
import io
from openpyxl import Workbook

from database import get_db, Usuario, Ingreso, Egreso, Material, Empleado, Deuda, ConfigUI, Log
from auth import (
    authenticate_user, create_access_token, get_current_user,
    get_current_admin, get_current_superadmin, get_password_hash,
    update_profile, update_password, admin_update_user
)
from ui_editor import get_ui_config, save_ui_config, activate_ui_config, list_ui_configs

app = FastAPI(title = "Taller Elohim")

app = FastAPI(title="Sistema de Gestion Empresarial")

# ==================== CREAR USUARIO AL INICIAR ====================
from auth import crear_usuario_inicial

@app.on_event("startup")
def startup_event():
    crear_usuario_inicial()
    
# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "https://mellow-dasik-1bb49e.netlify.app",
        "https://*.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"mensaje": "API de Gestion Empresarial funcionando", "version": "1.0.0"}

@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/api/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    token = create_access_token(data={"sub": user.username, "rol": user.rol})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "rol": user.rol,
            "nombre_completo": user.nombre_completo
        }
    }

@app.get("/api/me")
def get_me(current_user: Usuario = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "rol": current_user.rol,
        "nombre_completo": current_user.nombre_completo,
        "email": current_user.email
    }

@app.get("/api/perfil")
def get_perfil(current_user: Usuario = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "nombre_completo": current_user.nombre_completo,
        "email": current_user.email,
        "rol": current_user.rol
    }

@app.put("/api/perfil")
def update_perfil(nombre_completo: str = None, email: str = None, 
                  db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    user = update_profile(current_user.id, nombre_completo, email, db)
    return {"message": "Perfil actualizado"}

@app.post("/api/cambiar_password")
def cambiar_password(current_password: str, new_password: str, 
                     db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if update_password(current_user.id, current_password, new_password, db):
        return {"message": "Contraseña actualizada"}
    raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")

@app.get("/api/usuarios")
def get_usuarios(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_admin)):
    usuarios = db.query(Usuario).all()
    return [{"id": u.id, "username": u.username, "rol": u.rol, "nombre_completo": u.nombre_completo, "email": u.email, "activo": u.activo} for u in usuarios]

@app.post("/api/usuarios")
def crear_usuario(username: str, password: str, rol: str, nombre_completo: str, email: str,
                  db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_admin)):
    existente = db.query(Usuario).filter(Usuario.username == username).first()
    if existente:
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    nuevo = Usuario(
        username=username,
        password_hash=get_password_hash(password),
        rol=rol,
        nombre_completo=nombre_completo,
        email=email,
        activo=True
    )
    db.add(nuevo)
    db.commit()
    return {"message": "Usuario creado", "id": nuevo.id}

@app.delete("/api/usuarios/{usuario_id}")
def eliminar_usuario(usuario_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_admin)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if usuario.rol == "superadmin":
        raise HTTPException(status_code=403, detail="No se puede eliminar superadmin")
    db.delete(usuario)
    db.commit()
    return {"message": "Usuario eliminado"}

@app.get("/api/ingresos")
def get_ingresos(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return db.query(Ingreso).all()

@app.post("/api/ingresos")
def crear_ingreso(cliente: str, concepto: str, monto: float, categoria: str, fecha: str, referencia: str = "",
                  db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    fecha_obj = datetime.fromisoformat(fecha)
    semana = fecha_obj.isocalendar()[1]
    nuevo = Ingreso(
        numero_factura=f"FAC{datetime.now().strftime('%Y%m%d%H%M%S')}",
        fecha=fecha_obj,
        cliente=cliente,
        concepto=concepto,
        monto=monto,
        categoria=categoria,
        referencia=referencia,
        pagado=False,
        semana=semana,
        creado_por_id=current_user.id
    )
    db.add(nuevo)
    db.commit()
    return {"id": nuevo.id, "message": "Ingreso creado"}

@app.delete("/api/ingresos/{ingreso_id}")
def eliminar_ingreso(ingreso_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_admin)):
    ingreso = db.query(Ingreso).filter(Ingreso.id == ingreso_id).first()
    if not ingreso:
        raise HTTPException(status_code=404, detail="Ingreso no encontrado")
    db.delete(ingreso)
    db.commit()
    return {"message": "Ingreso eliminado"}

@app.get("/api/dashboard")
def get_dashboard(semana: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    ingresos = db.query(Ingreso).filter(Ingreso.semana == semana).all()
    total_ingresos = sum(i.monto for i in ingresos)
    materiales = db.query(Material).filter(Material.semana == semana).all()
    total_materiales = sum(m.costo_total for m in materiales)
    empleados = db.query(Empleado).filter(Empleado.semana == semana).all()
    total_sueldos = sum(e.total for e in empleados)
    total_egresos = total_materiales + total_sueldos
    utilidad = total_ingresos - total_egresos
    ingresos_categoria = {}
    for i in ingresos:
        ingresos_categoria[i.categoria] = ingresos_categoria.get(i.categoria, 0) + i.monto
    return {
        "total_ingresos": total_ingresos,
        "total_egresos": total_egresos,
        "total_materiales": total_materiales,
        "total_sueldos": total_sueldos,
        "utilidad": utilidad,
        "ingresos_categoria": ingresos_categoria,
        "num_ingresos": len(ingresos)
    }

@app.get("/api/materiales")
def get_materiales(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return db.query(Material).all()

@app.post("/api/materiales")
def crear_material(nombre: str, cantidad: float, costo_unitario: float, proveedor: str, fecha: str,
                   db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    fecha_obj = datetime.fromisoformat(fecha)
    semana = fecha_obj.isocalendar()[1]
    costo_total = cantidad * costo_unitario
    nuevo = Material(
        nombre=nombre,
        cantidad=cantidad,
        costo_unitario=costo_unitario,
        costo_total=costo_total,
        proveedor=proveedor,
        semana=semana,
        fecha=fecha_obj,
        creado_por_id=current_user.id
    )
    db.add(nuevo)
    db.commit()
    return {"id": nuevo.id, "message": "Material creado"}

@app.delete("/api/materiales/{material_id}")
def eliminar_material(material_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_admin)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    db.delete(material)
    db.commit()
    return {"message": "Material eliminado"}

@app.get("/api/empleados")
def get_empleados(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return db.query(Empleado).all()

@app.post("/api/empleados")
def crear_pago_empleado(nombre: str, dias_trabajados: int, pago_diario: float, fecha_pago: str,
                        db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    fecha_obj = datetime.fromisoformat(fecha_pago)
    semana = fecha_obj.isocalendar()[1]
    total = dias_trabajados * pago_diario
    nuevo = Empleado(
        nombre=nombre,
        dias_trabajados=dias_trabajados,
        pago_diario=pago_diario,
        total=total,
        semana=semana,
        fecha_pago=fecha_obj,
        pagado=True,
        creado_por_id=current_user.id
    )
    db.add(nuevo)
    db.commit()
    return {"id": nuevo.id, "message": "Pago registrado"}

@app.delete("/api/empleados/{empleado_id}")
def eliminar_empleado(empleado_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_admin)):
    empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()
    if not empleado:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    db.delete(empleado)
    db.commit()
    return {"message": "Pago eliminado"}

@app.get("/api/deudas")
def get_deudas(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return db.query(Deuda).all()

@app.post("/api/deudas")
def crear_deuda(acreedor: str, monto: float, fecha_vencimiento: str, nota: str = "",
                db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    nueva = Deuda(
        acreedor=acreedor,
        monto=monto,
        fecha_vencimiento=datetime.fromisoformat(fecha_vencimiento),
        estado="Pendiente",
        nota=nota,
        creado_por_id=current_user.id
    )
    db.add(nueva)
    db.commit()
    return {"id": nueva.id, "message": "Deuda creada"}

@app.put("/api/deudas/{deuda_id}")
def actualizar_deuda(deuda_id: int, estado: str, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    deuda = db.query(Deuda).filter(Deuda.id == deuda_id).first()
    if not deuda:
        raise HTTPException(status_code=404, detail="Deuda no encontrada")
    deuda.estado = estado
    db.commit()
    return {"message": "Deuda actualizada"}

@app.delete("/api/deudas/{deuda_id}")
def eliminar_deuda(deuda_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_admin)):
    deuda = db.query(Deuda).filter(Deuda.id == deuda_id).first()
    if not deuda:
        raise HTTPException(status_code=404, detail="Deuda no encontrada")
    db.delete(deuda)
    db.commit()
    return {"message": "Deuda eliminada"}

@app.get("/api/ui/config")
def get_ui_config_endpoint(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_superadmin)):
    return get_ui_config(db, current_user)

@app.post("/api/ui/config")
def save_ui_config_endpoint(config: dict, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_superadmin)):
    return save_ui_config(config, db, current_user)

# ==================== SETUP PUBLICO ====================

@app.get("/setup")
def setup(db: Session = Depends(get_db)):
    from auth import get_password_hash
    user = db.query(Usuario).filter(Usuario.username == "superadmin").first()
    if not user:
        superadmin = Usuario(
            username="superadmin",
            password_hash=get_password_hash("super123"),
            rol="superadmin",
            nombre_completo="Super Administrador",
            email="super@admin.com",
            activo=True
        )
        db.add(superadmin)
        db.commit()
        return {"message": "Usuario superadmin creado"}
    return {"message": "Usuario superadmin ya existe"}

if __name__ == "__main__":
    import uvicorn
    from auth import crear_usuario_inicial
    crear_usuario_inicial()
    uvicorn.run(app, host="0.0.0.0", port=8000)