import os
import sys
from PyQt5.QtWidgets import QMessageBox

def ler_AVL(filename):
    """Lê um arquivo .AVL, limpa os dados e extrai todos os parâmetros aerodinâmicos e geométricos."""
    
    # Determina o diretório base (funciona tanto no script .py quanto no .exe compilado)
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    with open(filename, 'r', encoding='utf-8') as f:
        linhas_cruas = f.readlines()

    # Remove comentários e linhas vazias
    linhas_limpas = []
    for linha in linhas_cruas:
        texto_util = linha.split('!')[0].split('|')[0].strip().split('#')[0].strip()
        if texto_util: 
            linhas_limpas.append(texto_util)

    if not linhas_limpas:
        return None

    # Cabeçalho
    aeronave = {
        "nome": linhas_limpas[0],
        "mach": float(linhas_limpas[1].split()[0]),
        "sym": list(map(float, linhas_limpas[2].split())),
        "ref_dim": list(map(float, linhas_limpas[3].split())),
        "ref_pos": list(map(float, linhas_limpas[4].split())),
        "superficies": []
    }

    i = 5
    superficie_atual = None

    while i < len(linhas_limpas):
        token = linhas_limpas[i].upper()

        if token == 'SURFACE':
            i += 1
            nome_surf = linhas_limpas[i]
            i += 1
            # Parâmetros de malha (Nchord, Cspace, Nspan, Sspace)
            mesh_params = list(map(float, linhas_limpas[i].split()))
            
            superficie_atual = {
                "nome": nome_surf,
                "mesh": mesh_params,
                "yduplicate": None,
                "translate": [0.0, 0.0, 0.0],
                "angle": 0.0,
                "secoes": []
            }
            aeronave["superficies"].append(superficie_atual)

        elif token == 'YDUPLICATE':
            i += 1
            superficie_atual["yduplicate"] = float(linhas_limpas[i].split()[0])

        elif token == 'TRANSLATE':
            i += 1
            superficie_atual["translate"] = list(map(float, linhas_limpas[i].split()))

        elif token == 'ANGLE':
            i += 1
            superficie_atual["angle"] = float(linhas_limpas[i].split()[0])

        elif token == 'SECTION':
            i += 1
            # Xle, Yle, Zle, Chord, Ainc
            valores = list(map(float, linhas_limpas[i].split()))
            secao = {
                "x": valores[0],
                "y": valores[1],
                "z": valores[2],
                "corda": valores[3],
                "ainc": valores[4] if len(valores) > 4 else 0.0,
                "afile": None,
                "claf": None,
                "cdcl": None,
                "controles": []
            }
            superficie_atual["secoes"].append(secao)

        elif token.startswith('AFILE'):
            # Verifica se o nome do arquivo está na mesma linha (ex: AFILE naca.dat) ou na próxima
            partes = linhas_limpas[i].split()
            if len(partes) > 1:
                nome_arquivo = partes[1].strip()
            else:
                i += 1
                nome_arquivo = linhas_limpas[i].strip()
                
            superficie_atual["secoes"][-1]["afile"] = nome_arquivo
            
            # --- Verificação---
            caminho_esperado = os.path.join(base_path, '_internal', nome_arquivo)
            
            if not os.path.isfile(caminho_esperado):
                # caixa de diálogo do PyQt5
                QMessageBox.warning(
                    None, 
                    "Aviso de Aerofólio Ausente", 
                    f"O arquivo de aerofólio '{nome_arquivo}' não foi encontrado na pasta '_internal'.\n\n"
                    "O AVL pode apresentar erros na simulação se este arquivo não estiver presente."
                )

        elif token == 'CLAF':
            i += 1
            superficie_atual["secoes"][-1]["claf"] = float(linhas_limpas[i].split()[0])

        elif token == 'CDCL':
            i += 1
            # CDCL geralmente tem 6 valores (CL1 CD1 CL2 CD2 CL3 CD3)
            superficie_atual["secoes"][-1]["cdcl"] = list(map(float, linhas_limpas[i].split()))

        elif token == 'CONTROL':
            i += 1
            # name, gain, Xhinge, XYZhvec (3 valores), SgnDup
            valores = linhas_limpas[i].split()
            ctrl = {
                "nome": valores[0],
                "gain": float(valores[1]),
                "hinge": float(valores[2]),
                "hvec": list(map(float, valores[3:6])) if len(valores) >= 6 else [0.0, 0.0, 0.0],
                "sgndup": float(valores[6]) if len(valores) >= 7 else 1.0
            }
            superficie_atual["secoes"][-1]["controles"].append(ctrl)

        i += 1

    return aeronave
