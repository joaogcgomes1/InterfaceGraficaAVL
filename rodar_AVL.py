import subprocess
import os


def gerar_e_executar_script(nome_avl,
                            nome_mass,
                            nome_run,
                            nome_st,
                            caso_idx=0):
    """
    Executa automaticamente o AVL e gera o arquivo .st

    Retorna:
        True  -> sucesso
        False -> falha
    """

    
    nome_avl = os.path.abspath(nome_avl)
    nome_mass = os.path.abspath(nome_mass)
    nome_run = os.path.abspath(nome_run)
    nome_st_saida = os.path.abspath(nome_st)

    # Executável AVL no mesmo diretório deste arquivo
    pasta_script = os.path.dirname(os.path.abspath(__file__))
    avl_exe = os.path.join(pasta_script, "avl352.exe")

    if not os.path.exists(avl_exe):
        print(f"AVL não encontrado: {avl_exe}")
        return False

    # Script de comandos do AVL
    comandos = [
        f"LOAD {nome_avl}",
        f"MASS {nome_mass}",
        "MSET",
        "0",
        "CASE",
        nome_run,
        "OPER",
        str(caso_idx + 1),  # Seleciona o caso 
        "X",
        "ST",
        nome_st,
    ]

    # Se o arquivo já existir, overwrite
    if os.path.exists(nome_st):
        comandos.append("O")

    comandos.append("")
    comandos.append("QUIT")

    script_conteudo = "\n".join(comandos)

    arquivo_comando = os.path.join(pasta_script, "comando.txt")

    with open(arquivo_comando, "w", newline="\n") as f:
        f.write(script_conteudo)

    print("\n===== SCRIPT AVL =====")
    print(script_conteudo)
    print("======================\n")

    try:

        with open(arquivo_comando, "r") as stdin_file:

            resultado = subprocess.run(
                [avl_exe],
                stdin=stdin_file,
                capture_output=True,
                text=True,
                cwd=pasta_script
            )

        print("\n===== STDOUT AVL =====")
        print(resultado.stdout)

        print("\n===== STDERR AVL =====")
        print(resultado.stderr)

        if resultado.returncode != 0:
            print(f"AVL retornou código {resultado.returncode}")
            return False

        if not os.path.exists(nome_st):
            print(f"Arquivo .st não foi gerado: {nome_st}")
            return False

        print(f"Arquivo gerado com sucesso: {nome_st}")
        return True

    except Exception as e:
        print(f"Erro ao executar AVL: {e}")
        return False
