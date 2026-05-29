import hashlib
import secrets
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import SessionLocal, get_db, Usuario
from sqlalchemy.orm import Session

SECRET_KEY = "tu_clave_secreta_muy_segura_cambiar_en_produccion"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

security = HTTPBearer()

def get_password_hash(password):
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode())
    return f"{salt}:{hash_obj.hexdigest()}"

def verify_password(plain_password, hashed_password):
    try:
        salt, hash_value = hashed_password.split(":")
        hash_obj = hashlib.sha256((plain_password + salt).encode())
        return hash_obj.hexdigest() == hash_value
    except:
        return False

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(Usuario).filter(Usuario.username == username, Usuario.activo == True).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(Usuario).filter(Usuario.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_admin(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    return current_user

def get_current_superadmin(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol != "superadmin":
        raise HTTPException(status_code=403, detail="Se requieren permisos de superadmin")
    return current_user

def update_profile(user_id: int, nombre_completo: str = None, email: str = None, db: Session = None):
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        return None
    
    if nombre_completo:
        user.nombre_completo = nombre_completo
    if email:
        user.email = email
    
    db.commit()
    db.refresh(user)
    return user

def update_password(user_id: int, current_password: str, new_password: str, db: Session = None):
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        return False
    
    if not verify_password(current_password, user.password_hash):
        return False
    
    user.password_hash = get_password_hash(new_password)
    db.commit()
    return True

def admin_update_user(user_id: int, nombre_completo: str = None, email: str = None, rol: str = None, 
                      new_password: str = None, db: Session = None, admin_user = None):
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        return None
    
    if nombre_completo:
        user.nombre_completo = nombre_completo
    if email:
        user.email = email
    if rol and admin_user.rol == "superadmin":
        user.rol = rol
    if new_password:
        user.password_hash = get_password_hash(new_password)
    
    db.commit()
    db.refresh(user)
    return user

def crear_usuario_inicial():
    db = SessionLocal()
    try:
        superadmin = db.query(Usuario).filter(Usuario.username == "superadmin").first()
        if not superadmin:
            superadmin = Usuario(
                username="superadmin",
                password_hash=get_password_hash("super123"),
                rol="superadmin",
                nombre_completo="Super Administrador",
                email="superadmin@empresa.com",
                activo=True
            )
            db.add(superadmin)
            
            admin = Usuario(
                username="admin",
                password_hash=get_password_hash("admin123"),
                rol="admin",
                nombre_completo="Administrador",
                email="admin@empresa.com",
                activo=True
            )
            db.add(admin)
            
            trabajador = Usuario(
                username="trabajador1",
                password_hash=get_password_hash("trabajador123"),
                rol="trabajador",
                nombre_completo="Juan Perez",
                email="juan@empresa.com",
                activo=True
            )
            db.add(trabajador)
            
            db.commit()
            print("Usuarios creados correctamente")
    except Exception as e:
        print(f"Error al crear usuarios: {e}")
        db.rollback()
    finally:
        db.close()