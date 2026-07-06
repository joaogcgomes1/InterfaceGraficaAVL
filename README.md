# Manual do Usuário - Interface Gráfica para Athena Vortex Lattice (AVL)

**Autor:** João Gabriel Cerqueira Gomes
**Orientador:** Joel Laguárdia Campos Reis

Este documento serve como guia completo para a utilização da Interface Gráfica do AVL (Athena Vortex Lattice) desenvolvida em Python. O programa permite carregar arquivos geométricos, de massa e de execução, configurar casos de voo, inspecionar os dados lidos, visualizar o modelo geométrico em 3D e executar análises de estabilidade de forma simplificada e visual.

---

## Introdução

A **Interface Gráfica para AVL** foi criada para facilitar o fluxo de trabalho em análises aerodinâmicas e de estabilidade. O software atua como uma interface que interage de maneira invisível com o AVL, poupando o usuário da necessidade de utilizar o terminal de comandos.

### Pré-requisitos de Execução
Para garantir o correto funcionamento do programa, assegure-se de que:
* O executável original do AVL (`avl352.exe`) esteja localizado na pasta `_internal/`.
* Os arquivos de perfis aerodinâmicos (.dat) citados no seu modelo estejam localizados dentro da pasta `_internal/`. O software emitirá um aviso caso algum perfil esteja ausente.

---

## A Interface Principal

A interface é dividida em quatro abas de navegação principais localizadas na barra superior. É necessário carregar os dados nas primeiras abas para desbloquear as seguintes.

### Aba 1: Início / Arquivos
Esta é a tela principal onde os arquivos de entrada são configurados.

* **1. Modelo Aerodinâmico e Físico:** Você irá carregar os arquivos de dados da sua aeronave. Utilize **Carregar Geometria (.AVL)** para carregar as dimensões, superfícies e perfis da aeronave, e **Carregar Inércia (.MASS)** para ler o arquivo contendo massas, centro de gravidade e tensores de inércia.
* **2. Configuração do Caso de Voo:** Você pode **Carregar arquivo .RUN** (importando configurações elaboradas no formato tradicional do AVL) ou utilizar a **Configuração Manual**. O modo manual permite definir diretamente na interface as condições cinemáticas (fixar Sustentação ou Ângulo de Ataque $\alpha$, ângulo de derrapagem $\beta$, Mach e taxas de rotação p, q, r). Você também pode definir a deflexão das superfícies de controle ou transformá-las em variáveis de trimagem (ex: ajustar o profundor automaticamente para zerar o momento de arfagem $C_m$). O programa gerará um arquivo `.run` automático baseado nestas escolhas.
* **3. Executar Análise:** Ao clicar no botão verde de execução, a interface construirá um script, acionará o `avl352.exe` em segundo plano, coletará os resultados e gerará um arquivo de saída `.st`.

### Aba 2: Tabela de Dados
Após carregar os arquivos na primeira aba, esta tela é desbloqueada. Ela serve como uma ferramenta de conferência (Debug) para garantir que o AVL compreendeu corretamente o que foi modelado. A tela é dividida em sub-abas:

* **Dados Gerais:** Mostra área alar, corda média, envergadura, posição do CG/referência e condições de simetria geométrica.
* **Superfícies (Asas/Empenagens):** Lista todas as superfícies. Ao clicar em uma superfície, as tabelas inferiores revelam as *Seções* (com suas respectivas cordas e incidências) e os *Controles* mapeados (com vetores de articulação).
* **Propriedades de Massa:** Exibe componentes do tensor de inércias ($I_{xx}$, $I_{yy}$, $I_{zz}$, etc.) e variáveis ambientais lidas do arquivo `.MASS`.
* **Casos de Voo (.RUN):** Tabela mostrando todas as restrições operacionais e variáveis ativas no caso selecionado.

---

## Visualização 3D

Assim que um arquivo geométrico `.AVL` for carregado, o programa criará um modelo 3D da geometria descrita. 

### Controles do Mouse
* **Botão Esquerdo (Segurar e Arrastar):** Rotaciona a aeronave em torno do seu centroide.
* **Botão Direito (Segurar e Arrastar):** Translada a câmera no plano horizontal e vertical.
* **Roda do Mouse (Scroll):** Aplica zoom in / zoom out.

### Atalhos de Teclado
Para facilitar a inspeção geométrica, os seguintes atalhos estão mapeados:

| Tecla | Ação |
| :---: | :--- |
| **1** | Visualização Frontal (Vista Y-Z) |
| **2** | Visualização Lateral Direita (Vista X-Z) |
| **3** | Visualização Superior (Planta - Vista X-Y) |
| **4** | Visualização Traseira |
| **R** | Reseta a câmera para a posição e zoom isométricos padrão |
| **W** | Alterna entre os modos de exibição Malha *(Wireframe)* e Sólido |

> **Nota:** As superfícies de comando são mostradas na geometria por meio de seções de cor mais escura nas superfícies.

---

## Análise de Estabilidade e Resultados

Após executar a análise (Aba 1) com sucesso, a interface lerá o arquivo `.st` gerado e preencherá a última aba com os resultados processados.

### Condição de Voo / Trimagem
Esta janela é crucial para avaliar se a aeronave atingiu a condição de equilíbrio. Ela apresenta as forças e momentos adimensionais e dimensionais. As informações essenciais disponíveis são:

* **Totais de Equilíbrio:** Valores finais de $C_L$, $C_D$, $C_Y$, $C_l$, $C_m$ e $C_n$ para verificar a condição de equilíbrio.
* **Ponto Neutro manche fixo ($X_{np}$):** O programa destaca essa variável, essencial para garantida da estabilidade longitudinal. Representa a posição do centro de gravidade que torna a estabilidade estática longitudinal neutra.
* **Estabilidade Espiral:** Calculada a partir da relação $C_{l_b} \cdot C_{n_r} / C_{l_r} \cdot C_{n_b}$. O software indica visualmente com "Estável" (verde) ou "Instável" (vermelho) dependendo de seu valor.
* **Deflexão Efetiva de Controles:** Os ângulos finais, em graus, que os comandos precisaram atingir (caso não tenham sido travados manualmente) para manter o voo nivelado.

### Derivadas Aerodinâmicas
O AVL extrai um amplo conjunto de derivadas de estabilidade (estado e controle). Nesta sub-aba, a interface separa as derivadas agrupando-as por coeficientes aerodinâmicos. Todas as derivadas são mostradas em **rad⁻¹**.

* **Observação:** O AVL originalmente exporta as derivadas em relação à deflexão das superfícies de comando na unidade **°⁻¹** (1/grau). As derivadas mostradas na interface correspondem ao valor já corrigido para **rad⁻¹**.
