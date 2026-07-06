import re

def ler_RUN(filename):
    """Lê um arquivo .run do AVL, limpa artefatos e extrai múltiplos casos."""
    with open(filename, 'r', encoding='utf-8') as f:
        texto = f.read()
    
    # limpa o texto
    texto = re.sub(r'\s*\n\s*=\s*', ' = ', texto)
    
    # Divide o arquivo em blocos começando por "Run case"

    partes = re.split(r'(Run case\s+\d+:)', texto)
    
    lista_casos = []
    caso_atual = None
    
    
    for i in range(1, len(partes), 2):
        nome_caso = partes[i].strip()
        conteudo_caso = partes[i+1]
        
        dados_caso = {
            "run_case": nome_caso,
            "restricoes": [],
            "parametros": {}
        }
        
        for linha in conteudo_caso.splitlines():
            l = linha.strip()
            if not l or "---" in l:
                continue
                
            # Restrições
            if "->" in l:
                match = re.match(r'([a-zA-Z0-9_/]+)\s*->\s*([a-zA-Z0-9_\s/]+)\s*=\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)', l)
                if match:
                    dados_caso["restricoes"].append({
                        "variavel": match.group(1).strip(),
                        "alvo": match.group(2).strip(),
                        "valor": float(match.group(3))
                    })
                continue
                
            # Parâmetros
            if "=" in l:
                match = re.match(r'([a-zA-Z0-9_\.\s/]+)\s*=\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)(?:\s+([a-zA-Z0-9_\^/\-]+))?', l)
                if match:
                    chave = match.group(1).strip()
                    valor = float(match.group(2))
                    unidade = match.group(3).strip() if match.group(3) else ""
                    dados_caso["parametros"][chave] = {
                        "valor": valor,
                        "unidade": unidade
                    }
        lista_casos.append(dados_caso)
        
    return lista_casos
