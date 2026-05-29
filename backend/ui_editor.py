from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, ConfigUI
from auth import get_current_superadmin
import json
from datetime import datetime

def get_ui_config(db: Session = Depends(get_db), current_user = Depends(get_current_superadmin)):
    config_activa = db.query(ConfigUI).filter(ConfigUI.activa == True).first()
    if config_activa:
        return json.loads(config_activa.config_json)
    return {
        "titulo_sistema": "Sistema de Gestion Empresarial",
        "color_principal": "#2E4053",
        "mostrar_dashboard": True,
        "mostrar_ingresos": True,
        "mostrar_materiales": True,
        "mostrar_empleados": True,
        "mostrar_deudas": True,
        "mostrar_usuarios": True
    }

def save_ui_config(config: dict, db: Session = Depends(get_db), current_user = Depends(get_current_superadmin)):
    nueva_config = ConfigUI(
        version=config.get("version", "1.0"),
        config_json=json.dumps(config),
        activa=False,
        creado_en=datetime.now()
    )
    db.add(nueva_config)
    db.commit()
    db.refresh(nueva_config)
    return {"message": "Configuracion guardada", "id": nueva_config.id}

def activate_ui_config(config_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_superadmin)):
    db.query(ConfigUI).update({"activa": False})
    config = db.query(ConfigUI).filter(ConfigUI.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuracion no encontrada")
    config.activa = True
    db.commit()
    return {"message": "Configuracion activada"}

def list_ui_configs(db: Session = Depends(get_db), current_user = Depends(get_current_superadmin)):
    configs = db.query(ConfigUI).order_by(ConfigUI.creado_en.desc()).all()
    return [{"id": c.id, "version": c.version, "activa": c.activa, "creado_en": c.creado_en.isoformat()} for c in configs]