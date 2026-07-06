def ler_MASS(filename):
    """Lê um arquivo .MASS do AVL, extrai os parâmetros e captura as strings de unidades."""
    with open(filename, 'r', encoding='utf-8') as f:
        linhas_cruas = f.readlines()

    linhas_limpas = []
    for linha in linhas_cruas:
        texto_util = linha.split('!')[0].split('|')[0].strip().split('#')[0].strip()
        if texto_util:
            linhas_limpas.append(texto_util)

    if not linhas_limpas:
        return None

    dados_massa = {
        "Lunit": 1.0,
        "Munit": 1.0,
        "Tunit": 1.0,
        "g": 9.81,
        "rho": 1.225,
        "massa": 0.0,
        "cg": [0.0, 0.0, 0.0],
        "inercias": [0.0, 0.0, 0.0],
        "produtos_inercia": [0.0, 0.0, 0.0],
        "unidades": {}  
    }

    linha_valores_massa = None

    for linha in linhas_limpas:
        tokens = linha.split()
        if not tokens:
            continue

        if len(tokens) >= 3 and tokens[1] == '=':
            chave = tokens[0]
            try:
                valor = float(tokens[2])
                if chave in dados_massa:
                    dados_massa[chave] = valor
                
                if len(tokens) > 3:
                    dados_massa["unidades"][chave] = tokens[3]
            except ValueError:
                pass
            continue

        try:
            float(tokens[0])
            linha_valores_massa = tokens
        except ValueError:
            continue

    if linha_valores_massa:
        v = list(map(float, linha_valores_massa))
        if len(v) >= 7:
            dados_massa["massa"] = v[0]
            dados_massa["cg"] = [v[1], v[2], v[3]]
            dados_massa["inercias"] = [v[4], v[5], v[6]]
            if len(v) >= 10:
                dados_massa["produtos_inercia"] = [v[7], v[8], v[9]]

    return dados_massa
