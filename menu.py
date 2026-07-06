import sys
import os
from PyQt5.QtWidgets import (QAbstractSpinBox, QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QMessageBox, QTreeWidget, 
                             QTreeWidgetItem, QFrame, QStackedWidget, QTabWidget, QHeaderView,
                             QGroupBox, QComboBox, QRadioButton, QDoubleSpinBox, QFormLayout,
                             QCheckBox, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QSurfaceFormat, QColor, QIcon

# scripts auxiliares
from ler_avl import ler_AVL
from ler_mass import ler_MASS
from ler_run import ler_RUN
from ler_st import ler_ST
from gerar_tela import Viewer3D
from rodar_AVL import gerar_e_executar_script


class AVLWorker(QThread):
    concluido = pyqtSignal(bool, str)

    def __init__(self, nome_avl, nome_mass, nome_run, nome_st_saida, caso_idx):
        super().__init__()
        self.nome_avl = nome_avl
        self.nome_mass = nome_mass
        self.nome_run = nome_run
        self.nome_st_saida = nome_st_saida
        self.caso_idx = caso_idx

    def run(self):
        try:
            sucesso = gerar_e_executar_script(
                self.nome_avl,
                self.nome_mass,
                self.nome_run,
                self.nome_st_saida,
                self.caso_idx
            )
            self.concluido.emit(sucesso, "Processo concluído")
        except Exception as e:
            self.concluido.emit(False, str(e))


class InterfaceAVL(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Athena Vortex Lattice - Análise de Arquivos")
        self.resize(1000, 720)

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avl_logo.ico")
        self.setWindowIcon(QIcon(icon_path))

        self.filename = None
        self.filename_mass = None
        self.filename_run = None
        self.filename_st = None
        self.aeronave = None
        self.massa_dados = None
        self.run_dados = []
        self.st_dados = None
        self.manual_controls_ui = {}

        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; font-family: 'Segoe UI'; }
            QFrame#TopBar { background-color: #2b2b2b; }
            QPushButton.NavBtn {
                background-color: #3c3c3c; color: #e0e0e0; border: none;
                padding: 10px 20px; font-weight: bold; font-family: 'Segoe UI';
            }
            QPushButton.NavBtn:hover { background-color: #4a4a4a; }
            QPushButton.NavBtn:checked { background-color: #4e7ca8; color: white; }
            QPushButton.NavBtn:disabled { background-color: #2b2b2b; color: #666666; }
            
            QPushButton.ActionBtn {
                color: white; border: none; padding: 10px 20px; font-weight: bold; font-family: 'Segoe UI';
            }
            QTreeWidget { 
                font-family: 'Segoe UI'; 
                font-size: 14px;
                border: 1px solid #c8c8c8; 
                alternate-background-color: #e8e8e8;
                background-color: #ffffff;
            }
            QHeaderView::section { 
                background-color: #e0e0e0; 
                font-size: 14px;
                padding: 4px; 
                border: 1px solid #c8c8c8; 
                font-family: 'Segoe UI';
                color: #2c2c2a;
            }
            QGroupBox {
                border: 1px solid #c8c8c8;
                border-radius: 4px;
                margin-top: 10px;
                font-family: 'Segoe UI';
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #2c2c2a;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.top_bar = QFrame()
        self.top_bar.setObjectName("TopBar")
        self.top_bar.setFixedHeight(45)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        self.btn_home = self.create_nav_button("Início / Arquivos")
        self.btn_info = self.create_nav_button("Tabela de Dados")
        self.btn_plot = self.create_nav_button("Visualização 3D")
        self.btn_estab = self.create_nav_button("Análise de Estabilidade")
        
        self.btn_info.setEnabled(False)
        self.btn_plot.setEnabled(False)
        self.btn_estab.setEnabled(False)

        top_layout.addWidget(self.btn_home)
        top_layout.addWidget(self.btn_info)
        top_layout.addWidget(self.btn_plot)
        top_layout.addWidget(self.btn_estab)
        top_layout.addStretch()

        main_layout.addWidget(self.top_bar)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.build_home_page()
        self.build_info_page()
        self.build_plot_page()
        self.build_estab_page()

        self.btn_home.clicked.connect(lambda: self.switch_page(0))
        self.btn_info.clicked.connect(lambda: self.switch_page(1))
        self.btn_plot.clicked.connect(lambda: self.switch_page(2))
        self.btn_estab.clicked.connect(lambda: self.switch_page(3))
        
        self.switch_page(0)

    def create_nav_button(self, text):
        btn = QPushButton(text)
        btn.setProperty("class", "NavBtn")
        btn.setCheckable(True)
        return btn

    def switch_page(self, index):
        self.btn_home.setChecked(index == 0)
        self.btn_info.setChecked(index == 1)
        self.btn_plot.setChecked(index == 2)
        self.btn_estab.setChecked(index == 3)
        self.stack.setCurrentIndex(index)

    # =========================================================================
    # PÁGINA 1: HOME E SELEÇÃO DE ARQUIVOS 
    # =========================================================================
    def build_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(40, 20, 40, 20)

        title = QLabel("Athena Vortex Lattice")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #2c2c2a;")
        title.setAlignment(Qt.AlignCenter)
        

        # PAINEL 1: Geometria e Massa
        gb_base = QGroupBox(" 1. Modelo Aerodinâmico e Físico (Obrigatório) ")
        lyt_base = QHBoxLayout(gb_base)
        
        btn_avl = QPushButton("Carregar Geometria (.AVL)")
        btn_avl.setProperty("class", "ActionBtn")
        btn_avl.setStyleSheet("background-color: #4e7ca8;")
        btn_avl.setCursor(Qt.PointingHandCursor)
        btn_avl.clicked.connect(self.selecionar_arquivo_avl)

        btn_mass = QPushButton("Carregar Inércia (.MASS)")
        btn_mass.setProperty("class", "ActionBtn")
        btn_mass.setStyleSheet("background-color: #4e7ca8;")
        btn_mass.setCursor(Qt.PointingHandCursor)
        btn_mass.clicked.connect(self.selecionar_arquivo_mass)
        
        lyt_base.addWidget(btn_avl)
        lyt_base.addWidget(btn_mass)

        # PAINEL 2: Caso de Voo
        gb_voo = QGroupBox(" 2. Configuração do Caso de Voo ")
        lyt_voo = QVBoxLayout(gb_voo)
        
        lyt_radios = QHBoxLayout()
        self.radio_run_arquivo = QRadioButton("Carregar arquivo .RUN")
        self.radio_run_arquivo.setChecked(True)
        self.radio_run_manual = QRadioButton("Configuração Manual Dinâmica")
        lyt_radios.addWidget(self.radio_run_arquivo)
        lyt_radios.addWidget(self.radio_run_manual)
        lyt_radios.addStretch()
        lyt_voo.addLayout(lyt_radios)
        
        self.stack_voo = QStackedWidget()
        
        # ---- Página A: Arquivo .RUN ----
        page_arquivo = QWidget()
        lyt_arq = QHBoxLayout(page_arquivo)
        lyt_arq.setContentsMargins(0, 10, 0, 0)
        
        btn_run = QPushButton("Carregar Execução (.RUN)")
        btn_run.setProperty("class", "ActionBtn")
        btn_run.setStyleSheet("background-color: #8da9c4;")
        btn_run.setCursor(Qt.PointingHandCursor)
        btn_run.clicked.connect(self.selecionar_arquivo_run)
        
        self.combo_run_home = QComboBox()
        self.combo_run_home.setEnabled(False)
        self.combo_run_home.setFixedWidth(250)
        
        lyt_arq.addWidget(btn_run)
        lyt_arq.addWidget(QLabel("Caso Selecionado:"))
        lyt_arq.addWidget(self.combo_run_home)
        lyt_arq.addStretch()
        self.stack_voo.addWidget(page_arquivo)
        
        # ---- Página B: entrada anual ----
        page_manual = QWidget()
        lyt_man = QVBoxLayout(page_manual)
        lyt_man.setContentsMargins(0, 10, 0, 0)
        
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        scroll_content = QWidget()
        lyt_scroll = QVBoxLayout(scroll_content)
        
        # Cinemática
        gb_cine = QGroupBox("Cinemática e Estado")
        lyt_cine = QFormLayout(gb_cine)
        
        self.combo_alvo_long = QComboBox()
        self.combo_alvo_long.addItems(["Fixar Alpha (°)", "Fixar Sustentação (CL)"])
        self.spin_alvo_long = QDoubleSpinBox(); self.spin_alvo_long.setRange(-100, 100); self.spin_alvo_long.setSingleStep(0.5); self.spin_alvo_long.setDecimals(4)

        self.spin_beta = QDoubleSpinBox(); self.spin_beta.setRange(-90, 90); self.spin_beta.setSingleStep(0.5); self.spin_beta.setDecimals(4)
        self.spin_mach = QDoubleSpinBox(); self.spin_mach.setRange(0, 5); self.spin_mach.setSingleStep(0.05); self.spin_mach.setDecimals(4)
        self.spin_pb = QDoubleSpinBox(); self.spin_pb.setRange(-10, 10); self.spin_pb.setSingleStep(0.01); self.spin_pb.setDecimals(4)
        self.spin_qc = QDoubleSpinBox(); self.spin_qc.setRange(-10, 10); self.spin_qc.setSingleStep(0.01); self.spin_qc.setDecimals(4)
        self.spin_rb = QDoubleSpinBox(); self.spin_rb.setRange(-10, 10); self.spin_rb.setSingleStep(0.01); self.spin_rb.setDecimals(4)

        lyt_cine.addRow(self.combo_alvo_long, self.spin_alvo_long)
        lyt_cine.addRow("Beta (°):", self.spin_beta)
        lyt_cine.addRow("Mach:", self.spin_mach)
        lyt_cine.addRow("Roll Rate (pb/2V):", self.spin_pb)
        lyt_cine.addRow("Pitch Rate (qc/2V):", self.spin_qc)
        lyt_cine.addRow("Yaw Rate (rb/2V):", self.spin_rb)
        
        # Controles Dinâmicos
        self.gb_ctrls = QGroupBox("Superfícies de Controle")
        self.lyt_ctrls = QFormLayout(self.gb_ctrls)
        self.lyt_ctrls.addRow(QLabel("Carregue o arquivo .AVL para gerar os controles dinâmicos."))
        
        lyt_scroll.addWidget(gb_cine)
        lyt_scroll.addWidget(self.gb_ctrls)
        lyt_scroll.addStretch()
        
        scroll.setWidget(scroll_content)
        lyt_man.addWidget(scroll)
        self.stack_voo.addWidget(page_manual)
        
        lyt_voo.addWidget(self.stack_voo)
        
        self.radio_run_arquivo.toggled.connect(lambda: self.stack_voo.setCurrentIndex(0))
        self.radio_run_manual.toggled.connect(lambda: self.stack_voo.setCurrentIndex(1))

        # PAINEL 3: Execução e Status
        self.btn_executar = QPushButton("3. Executar Análise de Estabilidade")
        self.btn_executar.setProperty("class", "ActionBtn")
        self.btn_executar.setStyleSheet("background-color: #5a8a5a; font-size: 16px; padding: 15px;")
        self.btn_executar.setCursor(Qt.PointingHandCursor)
        self.btn_executar.clicked.connect(self.executar_avl)

        status_frame = QFrame()
        status_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #c8c8c8; border-radius: 5px;")
        status_layout = QVBoxLayout(status_frame)
        status_title = QLabel("Status do Sistema")
        status_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        
        self.lbl_avl = QLabel("✖ Nenhum arquivo geométrico .AVL carregado")
        self.lbl_avl.setStyleSheet("color: #c0392b; font-size: 14px; border: none;")
        self.lbl_mass = QLabel("✖ Nenhum arquivo de massas .MASS carregado")
        self.lbl_mass.setStyleSheet("color: #c0392b; font-size: 14px; border: none;")
        self.lbl_exec = QLabel("Aguardando configuração de voo para executar...")
        self.lbl_exec.setStyleSheet("color: #888888; font-size: 14px; border: none;")

        status_layout.addWidget(status_title)
        status_layout.addWidget(self.lbl_avl)
        status_layout.addWidget(self.lbl_mass)
        status_layout.addWidget(self.lbl_exec)

        layout.addWidget(title)
        layout.addWidget(gb_base)
        layout.addWidget(gb_voo)
        layout.addWidget(self.btn_executar)
        layout.addWidget(status_frame)
        layout.addStretch()
        self.stack.addWidget(page)

    # =========================================================================
    # LEITURA DE ARQUIVOS 
    # =========================================================================
    def verificar_ativacao_tabelas(self):
        if self.filename or self.filename_mass or self.filename_run:
            self.btn_info.setEnabled(True)

    def selecionar_arquivo_avl(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecione o arquivo AVL", "", "Arquivos AVL (*.avl)")
        if arquivo:
            self.filename = arquivo
            try:
                self.aeronave = ler_AVL(self.filename)
                if self.aeronave:
                    self.verificar_ativacao_tabelas()
                    self.btn_plot.setEnabled(True)
                    self.lbl_avl.setText(f"✔ Arquivo AVL carregado: {os.path.basename(self.filename)}")
                    self.lbl_avl.setStyleSheet("color: #27ae60; font-size: 14px; border: none;")
                    self.build_info_page() 
                    self.build_plot_page()
                    self.atualizar_controles_manuais() # <--- Puxa controles manuais
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao ler arquivo AVL:\n{e}")

    def atualizar_controles_manuais(self):
        """Varre o AVL lido e recria os campos de controle dinamicamente no formulário Manual."""
        
        for i in reversed(range(self.lyt_ctrls.count())):
            item = self.lyt_ctrls.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                while item.layout().count():
                    subitem = item.layout().takeAt(0)
                    if subitem.widget(): subitem.widget().setParent(None)
                item.layout().setParent(None)
                
        self.manual_controls_ui = {}
        
        controles_unicos = set()
        for sup in self.aeronave.get('superficies', []):
            for sec in sup.get('secoes', []):
                for ctrl in sec.get('controles', []):
                    controles_unicos.add(ctrl.get('nome'))
                    
        if not controles_unicos:
            self.lyt_ctrls.addRow(QLabel("Nenhum controle mapeado na geometria (.AVL)."))
            return
            
        for nome in sorted(controles_unicos):
            spin = QDoubleSpinBox()
            spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
            spin.setRange(-100, 100)
            spin.setSingleStep(0.5)
            spin.setDecimals(4)
            chk = QCheckBox("Coeficiente de trimagem:")
            combo = QComboBox()
            combo.addItems(["Cm pitchmom", "Cl roll mom", "Cn yaw  mom"])
            combo.setEnabled(False)
            
            # Tenta inferir o alvo do trim pelo nome
            nl = nome.lower()
            if 'elev' in nl: combo.setCurrentText("Cm pitchmom")
            elif 'rud' in nl: combo.setCurrentText("Cn yaw  mom")
            elif 'ail' in nl: combo.setCurrentText("Cl roll mom")
            
            def toggle_estado(checked, s=spin, c=combo):
                s.setEnabled(not checked)
                c.setEnabled(checked)
                
            chk.toggled.connect(toggle_estado)
            
            row_lyt = QHBoxLayout()
            row_lyt.addWidget(spin)
            row_lyt.addWidget(chk)
            row_lyt.addWidget(combo)
            
            self.lyt_ctrls.addRow(f"{nome.capitalize()} (°):", row_lyt)
            self.manual_controls_ui[nome] = {'spin': spin, 'chk': chk, 'combo': combo}

    def selecionar_arquivo_mass(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecione o arquivo MASS", "", "Arquivos MASS (*.mass)")
        if arquivo:
            self.filename_mass = arquivo
            try:
                self.massa_dados = ler_MASS(self.filename_mass)
                self.lbl_mass.setText(f"✔ Arquivo MASS carregado: {os.path.basename(self.filename_mass)}")
                self.lbl_mass.setStyleSheet("color: #27ae60; font-size: 14px; border: none;")
                self.verificar_ativacao_tabelas()
                self.build_info_page()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao ler arquivo MASS:\n{e}")

    def selecionar_arquivo_run(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecione o arquivo RUN", "", "Arquivos RUN (*.run)")
        if arquivo:
            self.filename_run = arquivo
            try:
                self.run_dados = ler_RUN(arquivo)
                self.verificar_ativacao_tabelas()
                self.combo_run_home.clear()
                for i, caso in enumerate(self.run_dados):
                    nome = caso.get('run_case', f"Caso {i+1}")
                    self.combo_run_home.addItem(nome)
                self.combo_run_home.setEnabled(True)
                self.build_info_page()
                QMessageBox.information(self, "Sucesso", "Arquivo .RUN carregado com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao ler arquivo .RUN:\n{e}")

    # =========================================================================
    # GERAÇÃO DO .run MANUAL E EXECUÇÃO
    # =========================================================================
    def gerar_run_manual(self, filepath):
        """Escreve um arquivo .run temporário com as restrições informadas na UI."""
        tipo_cond = self.combo_alvo_long.currentText()
        valor_alpha = self.spin_alvo_long.value()

        if tipo_cond == "Fixar Alpha (°)":
            res_alpha = f" alpha        ->  alpha       =   {valor_alpha:.5f}"
        else:
            res_alpha = f" alpha        ->  CL          =   {valor_alpha:.5f}"

        conteudo = f"""
---------------------------------------------
Run case  1:  Caso Manual 

{res_alpha}
 beta         ->  beta        =   {self.spin_beta.value():.5f}
 pb/2V        ->  pb/2V       =   {self.spin_pb.value():.5f}
 qc/2V        ->  qc/2V       =   {self.spin_qc.value():.5f}
 rb/2V        ->  rb/2V       =   {self.spin_rb.value():.5f}
 mach         ->  mach        =   {self.spin_mach.value():.5f}
"""
        # Extrai os controles gerados dinamicamente
        for nome, ui in self.manual_controls_ui.items():
            if ui['chk'].isChecked():
                alvo = ui['combo'].currentText()
                conteudo += f" {nome:<12} ->  {alvo:<11} =   0.00000\n"
            else:
                val = ui['spin'].value()
                conteudo += f" {nome:<12} ->  {nome:<11} =   {val:.5f}\n"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(conteudo)
            
        # O sistema agora passa a usar esse arquivo como se tivesse sido carregado pelo usuário
        self.filename_run = filepath
        self.run_dados = ler_RUN(filepath)
        self.build_info_page()

    def executar_avl(self):
        faltando = []
        if not self.filename: faltando.append("• Geometria (.AVL)")
        if not self.filename_mass: faltando.append("• Distribuição de massas (.MASS)")
        
        if self.radio_run_arquivo.isChecked() and not self.filename_run: 
            faltando.append("• Arquivo de execução (.RUN) não selecionado.")

        if faltando:
            QMessageBox.warning(self, "Arquivos ausentes", "Por favor, conclua as etapas antes de executar:\n\n" + "\n".join(faltando))
            return

        base = os.path.splitext(self.filename)[0]
        
        if self.radio_run_manual.isChecked():
            caminho_manual = base + "_manual.run"
            self.gerar_run_manual(caminho_manual)
            caso_idx = 0
            nome_st = base + "_manual.st"
        else:
            caso_idx = self.combo_run_home.currentIndex() if self.combo_run_home.count() > 0 else 0
            base_run = os.path.splitext(self.filename_run)[0]
            nome_st = base_run + ".st"

        self.btn_executar.setEnabled(False)
        self.btn_executar.setStyleSheet("background-color: #3d5e3d; font-size: 16px; padding: 15px;")
        self.lbl_exec.setText("⏳  Executando o AVL...")
        self.lbl_exec.setStyleSheet("color: #e67e22; font-size: 14px; border: none; font-weight: bold;")

        self._avl_worker = AVLWorker(self.filename, self.filename_mass, self.filename_run, nome_st, caso_idx)
        self._avl_worker.concluido.connect(lambda ok, msg: self._ao_concluir_avl(ok, msg, nome_st))
        self._avl_worker.start()

    def _ao_concluir_avl(self, sucesso, mensagem, nome_st):
        self.btn_executar.setEnabled(True)
        self.btn_executar.setStyleSheet("background-color: #5a8a5a; font-size: 16px; padding: 15px;")

        if sucesso:
            self.lbl_exec.setText(f"✔  Análise de estabilidade concluída com sucesso.")
            self.lbl_exec.setStyleSheet("color: #27ae60; font-size: 14px; border: none; font-weight: bold;")
            try:
                self.filename_st = nome_st
                self.st_dados = ler_ST(self.filename_st)
                self.build_estab_page()
                self.btn_estab.setEnabled(True)
                resposta = QMessageBox.question(self, "Análise Concluída", f"{mensagem}\n\nDeseja abrir a aba de Resultados de Estabilidade?", QMessageBox.Yes | QMessageBox.No)
                if resposta == QMessageBox.Yes:
                    self.switch_page(3)
            except Exception as e:
                QMessageBox.warning(self, "Aviso", f"AVL executou, mas falhou ao ler o .st gerado:\n{e}")
        else:
            self.lbl_exec.setText("✖  Falha na convergência ou erro na execução.")
            self.lbl_exec.setStyleSheet("color: #c0392b; font-size: 14px; border: none; font-weight: bold;")
            QMessageBox.critical(self, "Erro na Execução", mensagem)

    # =========================================================================
    # FUNÇÕES DE TABELA (Helpers)
    # =========================================================================
    def preparar_tabela_limpa(self, colunas, larguras=None):
        tree = QTreeWidget()
        tree.setColumnCount(len(colunas))
        tree.setHeaderLabels(colunas)
        tree.setRootIsDecorated(False) 
        tree.setAlternatingRowColors(True)
        tree.setSelectionMode(QTreeWidget.SingleSelection)
        tree.setSelectionBehavior(QTreeWidget.SelectRows)
        if larguras:
            for i, larg in enumerate(larguras):
                tree.setColumnWidth(i, larg)
        return tree

    # =========================================================================
    # PÁGINA 2: TABELAS DE DADOS
    # =========================================================================
    def build_info_page(self):
        if self.stack.count() > 1:
            widget_to_remove = self.stack.widget(1)
            self.stack.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()

        page = QWidget()
        layout = QVBoxLayout(page)

        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #d1d5db; background: #f8f9fa;} QTabBar::tab { padding: 8px 20px; }")
        fonte_abas = QFont("Segoe UI", 9, QFont.Bold)
        tabs.tabBar().setFont(fonte_abas)

        # ABA 1: DADOS GERAIS
        tab_geral = QWidget()
        lyt_geral = QVBoxLayout(tab_geral)
        if self.aeronave:
            gb_cat_geral = QGroupBox(" 1. Categorias Globais ")
            lyt_cat_geral = QVBoxLayout(gb_cat_geral)
            self.tree_cat = self.preparar_tabela_limpa(["Categoria", "Descrição"], [250, 450])
            lyt_cat_geral.addWidget(self.tree_cat)
            
            gb_det_geral = QGroupBox(" 2. Variáveis Detalhadas ")
            lyt_det_geral = QVBoxLayout(gb_det_geral)
            self.tree_detalhe_geral = self.preparar_tabela_limpa(["Parâmetro do Arquivo (.AVL)", "Valor"], [250, 350])
            lyt_det_geral.addWidget(self.tree_detalhe_geral)
            
            lyt_geral.addWidget(gb_cat_geral)
            lyt_geral.addWidget(gb_det_geral)
            
            self.tree_cat.itemSelectionChanged.connect(self.atualizar_detalhes_gerais)
            QTreeWidgetItem(self.tree_cat, ["Configurações da análise", "Nome da aeronave, número de Mach e simetria aerodinâmica."])
            QTreeWidgetItem(self.tree_cat, ["Dimensões de Referência (Sref, Cref, Bref)", "Área alar, corda média e envergadura."])
            QTreeWidgetItem(self.tree_cat, ["Posição de Referência / CG (Xref, Yref, Zref)", "Coordenadas do ponto de referência aerodinâmico."])
            self.tree_cat.setCurrentItem(self.tree_cat.topLevelItem(0))
        else:
            lbl = QLabel("Nenhum arquivo AVL carregado."); lbl.setAlignment(Qt.AlignCenter); lyt_geral.addWidget(lbl)
        tabs.addTab(tab_geral, "Dados Gerais")

        # ABA 2: SUPERFÍCIES
        tab_sup = QWidget()
        lyt_sup = QVBoxLayout(tab_sup)
        if self.aeronave:
            gb_cat_sup = QGroupBox(" 1. Lista de Superfícies Mapeadas ")
            lyt_cat_sup = QVBoxLayout(gb_cat_sup)
            self.tree_sup = self.preparar_tabela_limpa(["ID / Nome", "Nchord", "Cspace", "Nspan", "Sspace", "Simetria geométrica lateral", "Translação da superfície (X,Y,Z)", "Incidência da superfície"], [130, 70, 70, 70, 70, 90, 140, 70])
            lyt_cat_sup.addWidget(self.tree_sup)
            
            self.tabs_sup_bottom = QTabWidget()
            self.tabs_sup_bottom.tabBar().setFont(fonte_abas)
            
            self.tree_sec = self.preparar_tabela_limpa(["Seção Nº", "Xle", "Yle", "Zle", "Corda local", "Incidência local", "Perfil aerodinâmico", "CLAF"], [80, 80, 80, 80, 80, 120, 150, 100])
            self.tree_ctrl = self.preparar_tabela_limpa(["Vinc. à Seção", "Nome do Controle", "Ganho", "Posição da articulação em porcentagem da corda local", "Vetor da articulação [X,Y,Z]", "SgnDup"], [100, 150, 100, 100, 180, 90])
            self.tabs_sup_bottom.addTab(self.tree_sec, " Seções da Superfície Selecionada ")
            self.tabs_sup_bottom.addTab(self.tree_ctrl, " Controles Vinc. às Seções ")
            
            lyt_sup.addWidget(gb_cat_sup)
            lyt_sup.addWidget(self.tabs_sup_bottom)
            
            self.tree_sup.itemSelectionChanged.connect(self.atualizar_tabelas_subordinadas)
            self.lista_mapeamento_sup = self.aeronave.get('superficies', [])
            for i, sup in enumerate(self.lista_mapeamento_sup):
                m = sup.get('mesh', [0.0, 0.0, 0.0, 0.0]) + [0.0]*4
                trans = ", ".join(map(str, sup.get('translate', [0.0, 0.0, 0.0])))
                valores_linha = [str(sup.get('nome', f"Surf {i+1}")), str(m[0]), str(m[1]), str(m[2]), str(m[3]), str(sup.get('yduplicate', "Não")), f"[{trans}]", str(sup.get('angle', 0.0))]
                QTreeWidgetItem(self.tree_sup, valores_linha)
                
            if self.tree_sup.topLevelItemCount() > 0:
                self.tree_sup.setCurrentItem(self.tree_sup.topLevelItem(0))
        else:
            lbl = QLabel("Nenhum arquivo AVL carregado."); lbl.setAlignment(Qt.AlignCenter); lyt_sup.addWidget(lbl)
        tabs.addTab(tab_sup, "Superfícies (Asas/Empenagens)")

        # ABA 3: PROPRIEDADES DE MASSA
        tab_mass = QWidget()
        lyt_mass = QVBoxLayout(tab_mass)
        if self.massa_dados:
            gb_cat_mass = QGroupBox(" 1. Categorias Físicas de Inércia ")
            lyt_cat_mass = QVBoxLayout(gb_cat_mass)
            self.tree_cat_mass = self.preparar_tabela_limpa(["Grupo de Variáveis", "Descrição dos Componentes Mecânicos"], [250, 450])
            lyt_cat_mass.addWidget(self.tree_cat_mass)
            
            gb_det_mass = QGroupBox(" 2. Componentes Numéricos e Escalares Selecionados ")
            lyt_det_mass = QVBoxLayout(gb_det_mass)
            self.tree_detalhe_mass = self.preparar_tabela_limpa(["Parâmetro do Arquivo (.MASS)", "Valor"], [250, 350])
            lyt_det_mass.addWidget(self.tree_detalhe_mass)
            
            lyt_mass.addWidget(gb_cat_mass)
            lyt_mass.addWidget(gb_det_mass)
            
            self.tree_cat_mass.itemSelectionChanged.connect(self.atualizar_detalhes_massa)
            QTreeWidgetItem(self.tree_cat_mass, ["Unidades/Propriedades Gerais", "Unidades e propriedades gerais (Lunit, Munit, Tunit, g, rho)."])
            QTreeWidgetItem(self.tree_cat_mass, ["Massa Total/Centro de Gravidade", "Massa e coordenadas do CG."])
            QTreeWidgetItem(self.tree_cat_mass, ["Momento/Produtos de Inércia", "Tensor principal de momentos de inércia (Ixx, Iyy, Izz)."])
            self.tree_cat_mass.setCurrentItem(self.tree_cat_mass.topLevelItem(0))
        else:
            lbl = QLabel("Nenhum arquivo de massa (.MASS) foi carregado.")
            lbl.setStyleSheet("color: #888888; font-style: italic;"); lbl.setAlignment(Qt.AlignCenter)
            lyt_mass.addWidget(lbl)
        tabs.addTab(tab_mass, "Propriedades de Massa")

        # ABA 4: CASOS DE VOO
        tab_run = QWidget()
        lyt_run = QVBoxLayout(tab_run)
        if self.run_dados:
            gb_cat_run = QGroupBox(" 1. Dados de Caso (Lidos ou Gerados) ")
            lyt_cat_run = QHBoxLayout(gb_cat_run)
            lyt_cat_run.addWidget(QLabel("Caso atual:"))
            
            self.combo_run_info = QComboBox()
            self.combo_run_info.setFixedWidth(300)
            for i, caso in enumerate(self.run_dados):
                self.combo_run_info.addItem(caso.get('run_case', f"Caso {i+1}"))
            self.combo_run_info.currentIndexChanged.connect(self.atualizar_detalhes_run)
            
            lyt_cat_run.addWidget(self.combo_run_info)
            lyt_cat_run.addStretch()
            
            gb_det_run = QGroupBox(" 2. Restrições e Parâmetros ")
            lyt_det_run = QVBoxLayout(gb_det_run)
            self.tree_detalhe_run = self.preparar_tabela_limpa(["Parâmetro / Variável", "Valor", "Unidade / Tipo"], [250, 150, 150])
            lyt_det_run.addWidget(self.tree_detalhe_run)
            
            lyt_run.addWidget(gb_cat_run)
            lyt_run.addWidget(gb_det_run)
            
            self.atualizar_detalhes_run()
        else:
            lbl = QLabel("Nenhum arquivo de execução (.RUN) foi carregado.")
            lbl.setStyleSheet("color: #888888; font-style: italic;"); lbl.setAlignment(Qt.AlignCenter)
            lyt_run.addWidget(lbl)
        tabs.addTab(tab_run, "Casos de Voo (.RUN)")

        layout.addWidget(tabs)
        self.stack.insertWidget(1, page)

    def atualizar_detalhes_gerais(self):
        self.tree_detalhe_geral.clear()
        selected = self.tree_cat.selectedItems()
        if not selected: return
        idx_linha = self.tree_cat.indexOfTopLevelItem(selected[0])
        
        sym = self.aeronave.get('sym', [0.0, 0.0])
        ref_dim = self.aeronave.get('ref_dim', [0.0, 0.0, 0.0])
        ref_pos = self.aeronave.get('ref_pos', [0.0, 0.0, 0.0])
        
        if idx_linha == 0:
            QTreeWidgetItem(self.tree_detalhe_geral, ["Nome da Aeronave", str(self.aeronave.get('nome', 'N/A'))])
            QTreeWidgetItem(self.tree_detalhe_geral, ["Mach", str(self.aeronave.get('mach', 0.0))])
            QTreeWidgetItem(self.tree_detalhe_geral, ["iYsym (Symetry X-Y)", str(sym[0])])
            QTreeWidgetItem(self.tree_detalhe_geral, ["iZsym (Symetry X-Z)", str(sym[1])])
        elif idx_linha == 1:
            QTreeWidgetItem(self.tree_detalhe_geral, ["Área de referência da asa", str(ref_dim[0])])
            QTreeWidgetItem(self.tree_detalhe_geral, ["Corda média aerodinâmica", str(ref_dim[1])])
            QTreeWidgetItem(self.tree_detalhe_geral, ["Envergadura", str(ref_dim[2])])
        elif idx_linha == 2:
            QTreeWidgetItem(self.tree_detalhe_geral, ["Coordenada X do ponto de referência", str(ref_pos[0])])
            QTreeWidgetItem(self.tree_detalhe_geral, ["Coordenada Y do ponto de referência", str(ref_pos[1])])
            QTreeWidgetItem(self.tree_detalhe_geral, ["Coordenada Z do ponto de referência", str(ref_pos[2])])

    def atualizar_tabelas_subordinadas(self):
        self.tree_sec.clear()
        self.tree_ctrl.clear()
        selected = self.tree_sup.selectedItems()
        if not selected: return
        
        idx = self.tree_sup.indexOfTopLevelItem(selected[0])
        superficie_alvo = self.lista_mapeamento_sup[idx]
        secoes = superficie_alvo.get('secoes', [])
        controles_encontrados = False
        
        for j, sec in enumerate(secoes):
            val_sec = [f"Seção #{j+1}", str(sec.get('x',0.0)), str(sec.get('y',0.0)), str(sec.get('z',0.0)), str(sec.get('corda',0.0)), str(sec.get('ainc',0.0)), str(sec.get('afile','Nenhum')), str(sec.get('claf','1.0'))]
            QTreeWidgetItem(self.tree_sec, val_sec)
            for ctrl in sec.get('controles', []):
                controles_encontrados = True
                hvec_str = ", ".join(map(str, ctrl.get('hvec', [0.0, 0.0, 0.0])))
                val_ctrl = [f"Seção #{j+1}", str(ctrl.get('nome', 'N/A')), str(ctrl.get('gain', 0.0)), str(ctrl.get('hinge', 0.0)), f"[{hvec_str}]", str(ctrl.get('sgndup', 1.0))]
                QTreeWidgetItem(self.tree_ctrl, val_ctrl)
                
        if not controles_encontrados:
            item = QTreeWidgetItem(self.tree_ctrl, ["-", "Nenhuma superfície móvel", "-", "-", "-", "-"])
            item.setForeground(1, QColor("gray"))

    def atualizar_detalhes_massa(self):
        self.tree_detalhe_mass.clear()
        selected = self.tree_cat_mass.selectedItems()
        if not selected: return
        idx_linha = self.tree_cat_mass.indexOfTopLevelItem(selected[0])
        
        m = self.massa_dados
        u = m.get("unidades", {})
        
        u_L = u.get("Lunit", "")
        u_M = u.get("Munit", "")
        u_T = u.get("Tunit", "")
        u_g = f"{u_L}/{u_T}²" if u_L and u_T else ""
        u_rho = f"{u_M}/{u_L}³" if u_M and u_L else ""
        u_in = f"{u_M}·{u_L}²" if u_M and u_L else ""
        
        if idx_linha == 0:
            QTreeWidgetItem(self.tree_detalhe_mass, ["Unidade de Comprimento", f"{m.get('Lunit','')} {u_L}".strip()])
            QTreeWidgetItem(self.tree_detalhe_mass, ["Unidade de Massa", f"{m.get('Munit','')} {u_M}".strip()])
            QTreeWidgetItem(self.tree_detalhe_mass, ["Unidade de Tempo", f"{m.get('Tunit','')} {u_T}".strip()])
            QTreeWidgetItem(self.tree_detalhe_mass, ["Aceleração Gravitacional", f"{m.get('g','')} {u_g}".strip()])
            QTreeWidgetItem(self.tree_detalhe_mass, ["Densidade do Ar ", f"{m.get('rho','')} {u_rho}".strip()])
        elif idx_linha == 1:
            QTreeWidgetItem(self.tree_detalhe_mass, ["Massa da Aeronave", f"{m.get('massa','')} {u_M}".strip()])
            QTreeWidgetItem(self.tree_detalhe_mass, ["Coordenada X do Centro de Gravidade", f"{m['cg'][0]} {u_L}".strip()])
            QTreeWidgetItem(self.tree_detalhe_mass, ["Coordenada Y do Centro de Gravidade", f"{m['cg'][1]} {u_L}".strip()])
            QTreeWidgetItem(self.tree_detalhe_mass, ["Coordenada Z do Centro de Gravidade", f"{m['cg'][2]} {u_L}".strip()])
        elif idx_linha == 2:
            QTreeWidgetItem(self.tree_detalhe_mass, ["Ixx", f"{m['inercias'][0]} {u_in}".strip()])
            QTreeWidgetItem(self.tree_detalhe_mass, ["Iyy", f"{m['inercias'][1]} {u_in}".strip()])
            QTreeWidgetItem(self.tree_detalhe_mass, ["Izz", f"{m['inercias'][2]} {u_in}".strip()])
            QTreeWidgetItem(self.tree_detalhe_mass, ["Ixy", f"{m['produtos_inercia'][0]} {u_in}".strip()])
            QTreeWidgetItem(self.tree_detalhe_mass, ["Ixz", f"{m['produtos_inercia'][1]} {u_in}".strip()])
            QTreeWidgetItem(self.tree_detalhe_mass, ["Iyz", f"{m['produtos_inercia'][2]} {u_in}".strip()])

    def atualizar_detalhes_run(self):
        if not hasattr(self, 'combo_run_info') or not self.run_dados: return
        self.tree_detalhe_run.clear()
        
        idx = self.combo_run_info.currentIndex()
        if idx < 0 or idx >= len(self.run_dados): return
        
        caso = self.run_dados[idx]
        
        for k, v in caso.get("parametros", {}).items():
            val = str(v.get("valor", ""))
            uni = str(v.get("unidade", ""))
            QTreeWidgetItem(self.tree_detalhe_run, [k, val, uni])
            
        for r in caso.get("restricoes", []):
            QTreeWidgetItem(self.tree_detalhe_run, [f"{r['variavel']} -> {r['alvo']}", str(r['valor']), "Restrição"])

    # =========================================================================
    # PÁGINA 3: VISUALIZAÇÃO 3D
    # =========================================================================
    def build_plot_page(self):
        if self.stack.count() > 2:
            widget_to_remove = self.stack.widget(2)
            self.stack.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if self.filename:
            self.viewer = Viewer3D(self.filename)
            layout.addWidget(self.viewer)
        else:
            layout.addWidget(QLabel("Carregue a geometria para ver o 3D.", alignment=Qt.AlignCenter))
            
        self.stack.insertWidget(2, page)

    # =========================================================================
    # PÁGINA 4: ANÁLISE DE ESTABILIDADE (.ST)
    # =========================================================================
    def simular_latex(self, texto):
        mapa_direto = {
            "Alpha": "&alpha;", "Beta": "&beta;", "Mach": "<i>M</i> (Mach)",
            "pb/2V": "<i>pb</i> / 2<i>V</i>", "qc/2V": "<i>qc</i> / 2<i>V</i>",
            "rb/2V": "<i>rb</i> / 2<i>V</i>", "p'b/2V": "<i>p'b</i> / 2<i>V</i>",
            "r'b/2V": "<i>r'b</i> / 2<i>V</i>", "e": "<i>e</i> (Oswald)",
            "Xnp": "X<sub>np</sub>", "Sref": "S<sub>ref</sub>", "Cref": "C<sub>ref</sub>",
            "Bref": "B<sub>ref</sub>", "Xref": "X<sub>ref</sub>", "Yref": "Y<sub>ref</sub>", "Zref": "Z<sub>ref</sub>"
        }
        if texto in mapa_direto: return mapa_direto[texto]
            
        if texto.startswith("C") and len(texto) >= 3:
            coef = texto[1]; sufixo = texto[2:]
            if "'" in sufixo: coef = coef + "'"; sufixo = sufixo.replace("'", "")
            
            if sufixo == 'a': sufixo = "&alpha;"
            elif sufixo == 'b': sufixo = "&beta;"
            elif 'd' in sufixo:
                idx_d = sufixo.find('d')
                if sufixo[idx_d+1:].isdigit():
                    prefixo_suf = sufixo[:idx_d]
                    num_controle = sufixo[idx_d+1:]
                    sufixo = f"{prefixo_suf}&delta;<sub>{num_controle}</sub>"
                
            return f"C<sub>{coef}{sufixo}</sub>"
            
        return texto

    def build_estab_page(self):
        if self.stack.count() > 3:
            widget_to_remove = self.stack.widget(3)
            self.stack.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()

        page = QWidget()
        layout = QVBoxLayout(page)
        
        if not self.st_dados:
            lbl = QLabel("Execute o AVL para gerar e visualizar a análise de estabilidade.", alignment=Qt.AlignCenter)
            lbl.setStyleSheet("color: #888888; font-style: italic;")
            layout.addWidget(lbl)
            self.stack.insertWidget(3, page)
            return

        d = self.st_dados
        fonte_abas = QFont("Segoe UI", 9, QFont.Bold)

        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #d1d5db; background: #f8f9fa;} QTabBar::tab { padding: 8px 20px; }")
        tabs.tabBar().setFont(fonte_abas)

        lista_controles = list(d.get("controles", {}).keys())

        # ABA 1: Condições de Voo & Trimagem
        tab_forcas = QWidget()
        lyt_forcas = QVBoxLayout(tab_forcas)

        lyt_row1 = QHBoxLayout() 
        lyt_row2 = QHBoxLayout() 

        gb_ref = QGroupBox(" Parâmetros de Referência ")
        lyt_ref = QVBoxLayout(gb_ref)
        tree_ref = self.preparar_tabela_limpa(["Parâmetro", "Valor"], [120, 100])
        ref_params = [
            ("Sref", d.get("Sref", d.get("referencia", {}).get("Sref", "—"))),
            ("Cref", d.get("Cref", d.get("referencia", {}).get("Cref", "—"))),
            ("Bref", d.get("Bref", d.get("referencia", {}).get("Bref", "—"))),
            ("Xref", d.get("Xref", d.get("referencia", {}).get("Xref", "—"))),
            ("Yref", d.get("Yref", d.get("referencia", {}).get("Yref", "—"))),
            ("Zref", d.get("Zref", d.get("referencia", {}).get("Zref", "—")))
        ]
        for param, val in ref_params: 
            item = QTreeWidgetItem(tree_ref, ["", str(val)])
            lbl_html = QLabel(self.simular_latex(param))
            lbl_html.setTextFormat(Qt.RichText)
            lbl_html.setStyleSheet("background: transparent; color: #2c2c2a; font-size: 18px;padding-left: 5px;")
            tree_ref.setItemWidget(item, 0, lbl_html)
        lyt_ref.addWidget(tree_ref)
        lyt_row1.addWidget(gb_ref)

        nome_caso = d.get('run_case', d.get('configuracao', 'Caso Atual'))
        gb_cin = QGroupBox(f" Estado de Voo ({nome_caso}) ")
        lyt_cin = QVBoxLayout(gb_cin)
        tree_cin = self.preparar_tabela_limpa(["Variável", "Valor"], [150, 100])
        cin_params = [
            ("Alpha", d.get("Alpha", "—")), ("Beta", d.get("Beta", "—")),
            ("Mach", d.get("Mach", "—")), ("pb/2V", d.get("pb_2V", d.get("pb/2V", "—"))),
            ("qc/2V", d.get("qc_2V", d.get("qc/2V", "—"))), ("rb/2V", d.get("rb_2V", d.get("rb/2V", "—"))),
            ("p'b/2V", d.get("p_prime_b_2V", d.get("p'b/2V", "—"))), ("r'b/2V", d.get("r_prime_b_2V", d.get("r'b/2V", "—")))
        ]
        for chave, val in cin_params:
            item = QTreeWidgetItem(tree_cin, ["", ""])
            lbl_html = QLabel(self.simular_latex(chave))
            lbl_html.setTextFormat(Qt.RichText)
            lbl_html.setStyleSheet("background: transparent; color: #2c2c2a; font-size: 18px;padding-left: 5px;")
            tree_cin.setItemWidget(item, 0, lbl_html)
            item.setText(1, f"{val:.5f}" if isinstance(val, float) else str(val))
        lyt_cin.addWidget(tree_cin)
        lyt_row1.addWidget(gb_cin)

        gb_trim = QGroupBox(" Análise de Trimagem (Coeficientes e Forças) ")
        lyt_trim = QVBoxLayout(gb_trim)
        tree_trim = self.preparar_tabela_limpa(["Coeficiente", "Valor"], [150, 120])
        forcas_dict = d.get("forcas", {})
        lista_trim = [
            "CXtot", "CYtot", "CZtot", "Cltot", "Cmtot", "Cntot",
            "Cl'tot", "Cn'tot", "CLtot", "CDtot", "CDvis", "CDind",
            "CLff", "CDff", "CYff", "e"
        ]
        for chave in lista_trim:
            chave_alt1 = chave.replace("'", "_prime_")
            valor = forcas_dict.get(chave, forcas_dict.get(chave_alt1, "—"))
            item = QTreeWidgetItem(tree_trim, ["", ""])
            lbl_html = QLabel(self.simular_latex(chave))
            lbl_html.setTextFormat(Qt.RichText)
            lbl_html.setStyleSheet("background: transparent; color: #2c2c2a; font-size: 18px;padding-left: 5px;")
            tree_trim.setItemWidget(item, 0, lbl_html)
            item.setText(1, f"{valor:.5f}" if isinstance(valor, float) else str(valor))
            
        xnp = d.get("Xnp")
        esp = d.get("estab_espiral")
        if xnp is not None:
            item_xnp = QTreeWidgetItem(tree_trim, ["", f"{xnp:.6f}"])
            lbl_xnp = QLabel(self.simular_latex("Xnp"))
            lbl_xnp.setTextFormat(Qt.RichText)
            lbl_xnp.setStyleSheet("background: transparent; color: #2c2c2a; font-size: 18px; padding-left: 5px;")
            tree_trim.setItemWidget(item_xnp, 0, lbl_xnp)
            item_xnp.setBackground(0, QColor("#e8f4f8")); item_xnp.setBackground(1, QColor("#e8f4f8"))
        if esp is not None:
            estavel = "✔ Estável" if esp > 1.0 else "✖ Instável"
            item_esp = QTreeWidgetItem(tree_trim, ["Estabilidade espiral", f"{esp:.6f}  [{estavel}]"])
            item_esp.setBackground(0, QColor("#e8f4f8")); item_esp.setBackground(1, QColor("#e8f4f8"))
            item_esp.setForeground(1, QColor("#27ae60") if esp > 1.0 else QColor("#c0392b"))
        lyt_trim.addWidget(tree_trim)
        lyt_row2.addWidget(gb_trim)

        gb_ctrl = QGroupBox(" Deflexão dos Controles ")
        lyt_ctrl = QVBoxLayout(gb_ctrl)
        tree_ctrl = self.preparar_tabela_limpa(["Superfície de Controle", "Deflexão (°)"], [180, 100])
        controles_dict = d.get("controles", {})
        if controles_dict:
            for nome, valor in controles_dict.items():
                nome_limpo = nome.lower().strip()
                if "tot" in nome_limpo or "ed0" in nome_limpo or "d0" in nome_limpo: continue
                if isinstance(valor, float):
                    QTreeWidgetItem(tree_ctrl, [nome.capitalize(), f"{valor:.5f}"])
                else:
                    QTreeWidgetItem(tree_ctrl, [nome.capitalize(), str(valor)])
        else:
            QTreeWidgetItem(tree_ctrl, ["—", "Nenhum controle mapeado"])
        lyt_ctrl.addWidget(tree_ctrl)
        lyt_row2.addWidget(gb_ctrl)

        lyt_row2.setStretchFactor(gb_trim, 2)
        lyt_row2.setStretchFactor(gb_ctrl, 1)
        lyt_forcas.addLayout(lyt_row1)
        lyt_forcas.addLayout(lyt_row2)
        tabs.addTab(tab_forcas, "Condição de Voo/Trimagem")

        # ABA 2: Derivadas Aerodinâmicas
        tab_deriv = QWidget()
        lyt_deriv = QVBoxLayout(tab_deriv)
        
        lyt_d_row1 = QHBoxLayout()
        lyt_d_row2 = QHBoxLayout()
        
        coefs_config = [
            ("CL", " Coeficiente de Sustentação (CL) ", lyt_d_row1),
            ("CD", " Coeficiente de Arrasto (CD) ", lyt_d_row1),
            ("Cm", " Momento de Arfagem (Cm) ", lyt_d_row1),
            ("CY", " Força Lateral (CY) ", lyt_d_row2),
            ("Cl", " Momento de Rolagem (Cl) ", lyt_d_row2),
            ("Cn", " Momento de Guinada (Cn) ", lyt_d_row2),
        ]
        
        todas_derivadas = {}
        for cat in ["deriv_alpha_beta", "deriv_pqr", "deriv_controle"]:
            todas_derivadas.update(d.get(cat, {}))
            
        for prefixo, titulo, layout_linha in coefs_config:
            gb = QGroupBox(titulo)
            lyt_gb = QVBoxLayout(gb)
            
            tree_alvo = self.preparar_tabela_limpa(["Símbolo", "Valor (rad⁻¹)"], [110, 100])
            lyt_gb.addWidget(tree_alvo)
            layout_linha.addWidget(gb)
            
            chaves_grupo = [k for k in todas_derivadas.keys() if k.startswith(prefixo)]
            
            for k in sorted(chaves_grupo):
                sufixo = k[len(prefixo):]
                
                if sufixo.startswith('d') and sufixo[1:].isdigit():
                    idx_controle = int(sufixo[1:]) - 1
                    if 0 <= idx_controle < len(lista_controles):
                        nome_real_controle = lista_controles[idx_controle].lower()
                        if "tot" in nome_real_controle or "ed0" in nome_real_controle: 
                            continue
                
                item_deriv = QTreeWidgetItem(tree_alvo, ["", f"{todas_derivadas[k]:.6f}"])
                lbl_latex = QLabel(self.simular_latex(k))
                lbl_latex.setTextFormat(Qt.RichText)
                lbl_latex.setStyleSheet("background: transparent; color: #2c2c2a; font-size: 18px; font-weight: bold; padding-left: 5px;")
                tree_alvo.setItemWidget(item_deriv, 0, lbl_latex)

        lyt_deriv.addLayout(lyt_d_row1)
        lyt_deriv.addLayout(lyt_d_row2)
        tabs.addTab(tab_deriv, "Derivadas Aerodinâmicas")

        layout.addWidget(tabs)
        self.stack.insertWidget(3, page)


if __name__ == "__main__":
    fmt = QSurfaceFormat()
    fmt.setSamples(8)
    fmt.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    
    _icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avl_logo.ico")
    app.setWindowIcon(QIcon(_icon_path))
    
    app.setFont(QFont("Segoe UI", 9))
    
    window = InterfaceAVL()
    window.show()
    
    sys.exit(app.exec_())