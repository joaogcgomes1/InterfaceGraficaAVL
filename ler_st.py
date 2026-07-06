import re
import math

def ler_ST(filepath):
    """
    Lê um arquivo .st gerado pelo AVL (comando ST no OPER).
    Retorna um dicionário estruturado com todas as seções do arquivo.
    """
    with open(filepath, "r") as f:
        conteudo = f.read()

    dados = {}

    # ── Cabeçalho ────────────────────────────────────────────────────────────
    dados["configuracao"]  = _extrair(r"Configuration:\s*(.+)", conteudo, str, "").strip()
    dados["run_case"]      = _extrair(r"Run case:\s*(.+)",      conteudo, str, "").strip()
    dados["n_superficies"] = _extrair(r"# Surfaces\s*=\s*(\d+)", conteudo, int, 0)
    dados["n_strips"]      = _extrair(r"# Strips\s*=\s*(\d+)",   conteudo, int, 0)
    dados["n_vortices"]    = _extrair(r"# Vortices\s*=\s*(\d+)", conteudo, int, 0)

    dados["Sref"] = _extrair(r"Sref\s*=\s*([\d.eE+\-]+)", conteudo, float, 0.0)
    dados["Cref"] = _extrair(r"Cref\s*=\s*([\d.eE+\-]+)", conteudo, float, 0.0)
    dados["Bref"] = _extrair(r"Bref\s*=\s*([\d.eE+\-]+)", conteudo, float, 0.0)
    dados["Xref"] = _extrair(r"Xref\s*=\s*([\-\d.eE+]+)", conteudo, float, 0.0)
    dados["Yref"] = _extrair(r"Yref\s*=\s*([\-\d.eE+]+)", conteudo, float, 0.0)
    dados["Zref"] = _extrair(r"Zref\s*=\s*([\-\d.eE+]+)", conteudo, float, 0.0)

    # ── Condição de voo ───────────────────────────────────────────────────────
    dados["Alpha"]  = _extrair(r"Alpha\s*=\s*([\-\d.eE+]+)", conteudo, float, 0.0)
    dados["Beta"]   = _extrair(r"Beta\s*=\s*([\-\d.eE+]+)",  conteudo, float, 0.0)
    dados["Mach"]   = _extrair(r"Mach\s*=\s*([\-\d.eE+]+)",  conteudo, float, 0.0)
    dados["pb_2V"]  = _extrair(r"pb/2V\s*=\s*([\-\d.eE+]+)", conteudo, float, 0.0)
    dados["qc_2V"]  = _extrair(r"qc/2V\s*=\s*([\-\d.eE+]+)", conteudo, float, 0.0)
    dados["rb_2V"]  = _extrair(r"rb/2V\s*=\s*([\-\d.eE+]+)", conteudo, float, 0.0)

    # ── Forças totais ─────────────────────────────────────────────────────────
    forcas_map = {
        "CXtot": r"CXtot\s*=\s*([\-\d.eE+]+)",
        "CYtot": r"CYtot\s*=\s*([\-\d.eE+]+)",
        "CZtot": r"CZtot\s*=\s*([\-\d.eE+]+)",
        "Cltot": r"Cltot\s*=\s*([\-\d.eE+]+)",
        "Cmtot": r"Cmtot\s*=\s*([\-\d.eE+]+)",
        "Cntot": r"Cntot\s*=\s*([\-\d.eE+]+)",
        "CLtot": r"CLtot\s*=\s*([\-\d.eE+]+)",
        "CDtot": r"CDtot\s*=\s*([\-\d.eE+]+)",
        "CDvis": r"CDvis\s*=\s*([\-\d.eE+]+)",
        "CDind": r"CDind\s*=\s*([\-\d.eE+]+)",
        "CLff":  r"CLff\s*=\s*([\-\d.eE+]+)",
        "CDff":  r"CDff\s*=\s*([\-\d.eE+]+)",
        "CYff":  r"CYff\s*=\s*([\-\d.eE+]+)",
        "e":     r"e\s*=\s*([\-\d.eE+]+)",
    }
    dados["forcas"] = {k: _extrair(pat, conteudo, float, 0.0) for k, pat in forcas_map.items()}

    # ── Deflexões de controle ─────────────────────────────────────────────────
    dados["controles"] = {}
    
    
    for m in re.finditer(r"([\w']+)\s*=\s*([\-\d.eE+]+)\s*$", conteudo, re.MULTILINE):
        nome = m.group(1)
        
        # 2. Filtra minúsculas, remove o "e" isolado e ignora derivadas como "ed01", "ed03"
        if nome[0].islower() and nome not in ("e",) and not re.match(r"^ed\d+$", nome):
            dados["controles"][nome] = float(m.group(2))

    # ── Derivadas de estabilidade: alpha / beta ───────────────────────────────
    derivadas_ab = [
        "CLa","CLb","CYa","CYb","CDa","CDb",
        "Cla","Clb","Cma","Cmb","Cna","Cnb",
    ]
    dados["deriv_alpha_beta"] = _extrair_derivadas(conteudo, derivadas_ab)

    # ── Derivadas de estabilidade: taxas p', q', r' ───────────────────────────
    derivadas_pqr = [
        "CLp","CLq","CLr","CYp","CYq","CYr","CDp","CDq","CDr",
        "Clp","Clq","Clr","Cmp","Cmq","Cmr","Cnp","Cnq","Cnr",
    ]
    dados["deriv_pqr"] = _extrair_derivadas(conteudo, derivadas_pqr)

    # ── Derivadas de controle (superfícies) ───────────────────────────────────
    dados["deriv_controle"] = _extrair_derivadas_controle(conteudo)

    # ── Ponto neutro e estabilidade espiral ───────────────────────────────────
    dados["Xnp"] = _extrair(r"Neutral point\s+Xnp\s*=\s*([\-\d.eE+]+)", conteudo, float, None)
    dados["estab_espiral"] = _extrair(
        r"Clb Cnr / Clr Cnb\s*=\s*([\-\d.eE+]+)", conteudo, float, None
    )

    return dados




def _extrair(padrao, texto, tipo, padrao_default):
    m = re.search(padrao, texto)
    if m:
        try:
            return tipo(m.group(1))
        except ValueError:
            pass
    return padrao_default


def _extrair_derivadas(texto, nomes):
    resultado = {}
    for nome in nomes:
        m = re.search(rf"{re.escape(nome)}\s*=\s*([\-\d.eE+]+)", texto)
        if m:
            resultado[nome] = float(m.group(1))
    return resultado


def _extrair_derivadas_controle(texto):
    """
    Extrai blocos de derivadas de controle.
    Converte os valores encontrados (originais em 1/grau no arquivo ST do AVL)
    para 1/radiano antes de salvar no dicionário.
    """
    resultado = {}
    
    # Fator de conversão de (1 / grau) para (1 / radiano)
    fator_rad = 180.0 / math.pi
    
    for m in re.finditer(r"([A-Za-z]+d\d+|CDffd\d+|ed\d+)\s*=\s*([\-\d.eE+]+)", texto):
        nome_derivada = m.group(1)
        valor_em_graus = float(m.group(2))
        
        # Multiplica pelo fator para obter em 1/rad
        resultado[nome_derivada] = valor_em_graus * fator_rad
        
    return resultado
