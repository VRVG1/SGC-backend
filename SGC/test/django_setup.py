import sys
import os
import django


def initWorkspace():
    sgc_path = "/home/ordep/programas/desarrollo_web/residencias/SGC/"
    project_path = f"{ sgc_path }SGC-backend/SGC/"
    sys.path.append(project_path)
    print(sys.path)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    django.setup()
