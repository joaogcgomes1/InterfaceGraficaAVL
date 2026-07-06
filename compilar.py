import os
import subprocess
import sys


subprocess.call([sys.executable, "-m", "pip", "install", "pyinstaller"])

if os.path.exists("build"):
    os.system("rmdir /s /q build")

if os.path.exists("dist"):
    os.system("rmdir /s /q dist")

comando = [
    sys.executable,
    "-m",
    "PyInstaller",

    "--noconfirm",
    "--clean",
    "--onedir",
    "--windowed",

    "--icon=avl_logo.ico",

    "--hidden-import=pygame",
    "--hidden-import=OpenGL",
    "--hidden-import=OpenGL.GL",
    "--hidden-import=OpenGL.GLU",

    "--collect-all=pygame",
    "--collect-all=OpenGL",

    "--add-data=avl_logo.ico;.",

    "--name=AVL",

    "menu.py"
]

# Executa compilacao
resultado = subprocess.call(comando)

print("\n" + "=" * 50)

if resultado == 0:
    print("COMPILACAO FINALIZADA COM SUCESSO")
    print("Executavel em:")
    print(r"dist\AVL\AVL.exe")
else:
    print("ERRO NA COMPILACAO")

print("=" * 50)
