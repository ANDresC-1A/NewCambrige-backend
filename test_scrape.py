import sys
import os
sys.path.append(r'd:\Cambrigue\NewCambrige-backend')

from app.core.database import SessionLocal
from app.modules.importacion.service import ImportacionService

db = SessionLocal()
try:
    service = ImportacionService(db)
    result = service.iniciar_scraping(usuario_id=1)
    print("RESULTADO FINAL:", result)
finally:
    db.close()
