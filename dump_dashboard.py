import sys
import os
import time

sys.path.append(r'd:\Cambrigue\NewCambrige-backend')
from app.core.database import SessionLocal
from app.modules.importacion.scraper.autenticacion import autenticar
from app.modules.importacion.scraper.logger import get_logger
from app.modules.importacion.scraper.driver_setup import crear_driver
from playwright.sync_api import sync_playwright

logger = get_logger("diagnostico_dashboard")

def main():
    db = SessionLocal()
    from app.modules.secretaria.models import CredencialesLogin as CredencialLogin
    cred = db.query(CredencialLogin).first()
    db.close()

    if not cred:
        print("No cred")
        return

    url = cred.url
    usuario = cred.nombre_usuario
    password = cred.password_hash 

    with sync_playwright() as p:
        browser, context, page = crear_driver(p)
        if autenticar(page, url=url, usuario=usuario, password=password, tipo_usuario="Administrativo"):
            print("Login exitoso. Dump dashboard...")
            time.sleep(3)
            
            # Guardar HTML principal
            with open("logs/dashboard_main.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            
            # Guardar HTML de cada frame
            for i, frame in enumerate(page.frames):
                try:
                    with open(f"logs/dashboard_frame_{i}_{frame.name}.html", "w", encoding="utf-8") as f:
                        f.write(frame.content())
                except Exception as e:
                    print(f"Error frame {i}: {e}")
                    
            page.screenshot(path="logs/dashboard.png", full_page=True)
            print("Dump completo en logs/")
        else:
            print("Login fallido")

if __name__ == "__main__":
    main()
