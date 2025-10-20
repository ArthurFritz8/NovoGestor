import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QSpinBox, QRadioButton, QButtonGroup,
    QCompleter, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QFileDialog
)
from PyQt6.QtCore import pyqtSignal, QStringListModel, Qt
from PyQt6.QtGui import QPixmap

from MeuEstoque.database.database_manager import DatabaseManager

class MoveStockWindow(QDialog):
    stock_changed = pyqtSignal() # Sinal renomeado para indicar movimentação de estoque

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Entrada/Saída de Estoque")
        self.setGeometry(150, 150, 800, 700) # Aumentar o tamanho da janela
        self.db = db_manager
        self.setStyleSheet(open("MeuEstoque/ui/styles.qss").read())
        self.products_data = {} # Para armazenar id: (nome, codigo)
        self.current_product_id = None
        self.selected_photo_path = None # Novo atributo para o caminho da foto
        self._setup_ui()
        self._load_products_table() # Carregar a tabela de produtos
        self._load_products_for_completer() # Manter o completer para o campo de busca

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Grupo para seleção de produto
        product_selection_group = QGroupBox("Seleção de Produto")
        product_selection_layout = QVBoxLayout(product_selection_group)

        # Layout de busca
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar produto por nome ou código...")
        self.search_input.textChanged.connect(self._load_products_table)
        search_layout.addWidget(QLabel("Buscar:"))
        search_layout.addWidget(self.search_input)
        product_selection_layout.addLayout(search_layout)

        # Tabela de produtos
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(4)
        self.product_table.setHorizontalHeaderLabels(["ID", "Nome do Produto", "Código", "Quantidade Atual"])
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.product_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.product_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.product_table.itemSelectionChanged.connect(self._on_product_selected_from_table)
        product_selection_layout.addWidget(self.product_table)
        
        main_layout.addWidget(product_selection_group)

        # Grupo para informações do produto selecionado
        product_info_group = QGroupBox("Informações do Produto Selecionado")
        product_info_layout = QVBoxLayout(product_info_group)
        self.selected_product_name_label = QLabel("Nome: ")
        self.selected_product_code_label = QLabel("Código: ")
        self.selected_product_qty_label = QLabel("Quantidade Atual: ")
        product_info_layout.addWidget(self.selected_product_name_label)
        product_info_layout.addWidget(self.selected_product_code_label)
        product_info_layout.addWidget(self.selected_product_qty_label)
        main_layout.addWidget(product_info_group)

        # Grupo para movimentação
        movement_group = QGroupBox("Registrar Movimentação")
        movement_layout = QVBoxLayout(movement_group)

        # Tipo de Movimentação
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Tipo de Movimentação:"))
        self.type_group = QButtonGroup(self)
        
        self.radio_entrada = QRadioButton("Entrada")
        self.radio_entrada.setChecked(True)
        self.type_group.addButton(self.radio_entrada)
        type_layout.addWidget(self.radio_entrada)

        self.radio_saida = QRadioButton("Saída")
        self.type_group.addButton(self.radio_saida)
        type_layout.addWidget(self.radio_saida)
        movement_layout.addLayout(type_layout)

        # Quantidade
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Quantidade:"))
        self.qty_spinbox = QSpinBox()
        self.qty_spinbox.setMinimum(1)
        self.qty_spinbox.setMaximum(999999)
        qty_layout.addWidget(self.qty_spinbox)
        movement_layout.addLayout(qty_layout)

        # Observação
        obs_layout = QHBoxLayout()
        obs_layout.addWidget(QLabel("Observação (opcional):"))
        self.obs_input = QLineEdit()
        obs_layout.addWidget(self.obs_input)
        movement_layout.addLayout(obs_layout)

        # Botões
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Registrar")
        self.save_btn.clicked.connect(self._register_movement)
        self.save_btn.setEnabled(False) # Desabilitado até um produto ser selecionado
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        movement_layout.addLayout(button_layout)
        
        main_layout.addWidget(movement_group)

    def _load_products_table(self):
        search_term = self.search_input.text()
        products = self.db.get_produtos(search_term)
        self.product_table.setRowCount(len(products))

        self.products_data = {} # Resetar para a nova busca
        for row_idx, product in enumerate(products):
            p_id, p_name, p_code, p_brand, p_qty, p_desc, p_location = product # Adicionado p_location
            display_name = f"{p_name} ({p_code})" if p_code else p_name
            self.products_data[display_name] = p_id # Manter para o completer, se necessário

            self.product_table.setItem(row_idx, 0, QTableWidgetItem(str(p_id)))
            self.product_table.setItem(row_idx, 1, QTableWidgetItem(p_name))
            self.product_table.setItem(row_idx, 2, QTableWidgetItem(p_code if p_code else 'N/A'))
            self.product_table.setItem(row_idx, 3, QTableWidgetItem(str(p_qty)))

    def _on_product_selected_from_table(self):
        selected_items = self.product_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            product_id = int(self.product_table.item(row, 0).text())
            product_name = self.product_table.item(row, 1).text()
            product_code = self.product_table.item(row, 2).text()
            product_qty = self.product_table.item(row, 3).text()

            self.current_product_id = product_id
            self.selected_product_name_label.setText(f"Nome: {product_name}")
            self.selected_product_code_label.setText(f"Código: {product_code}")
            self.selected_product_qty_label.setText(f"Quantidade Atual: {product_qty}")
            self.save_btn.setEnabled(True)
        else:
            self.current_product_id = None
            self.selected_product_name_label.setText("Nome: ")
            self.selected_product_code_label.setText("Código: ")
            self.selected_product_qty_label.setText("Quantidade Atual: ")
            self.save_btn.setEnabled(False)

    def _load_products_for_completer(self):
        products = self.db.get_all_products_for_combobox()
        product_names = []
        self.products_data = {}
        for p_id, p_name, p_code in products:
            display_name = f"{p_name} ({p_code})" if p_code else p_name
            product_names.append(display_name)
            self.products_data[display_name] = p_id
        
        completer_model = QStringListModel()
        completer_model.setStringList(product_names)
        self.completer = QCompleter(completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def _on_completer_activated(self, text):
        pass

    def _on_product_input_changed(self, text):
        self._load_products_table()

    def _register_movement(self):
        if not self.current_product_id:
            QMessageBox.warning(self, "Erro de Validação", "Por favor, selecione um produto válido na tabela.")
            return

        quantidade = self.qty_spinbox.value()
        tipo = "Entrada" if self.radio_entrada.isChecked() else "Saída"
        observacao = self.obs_input.text().strip()

        if quantidade <= 0:
            QMessageBox.warning(self, "Erro de Validação", "A quantidade deve ser maior que zero.")
            return

        if self.db.update_produto_quantity(self.current_product_id, quantidade, tipo, observacao): # Removido foto_path
            QMessageBox.information(self, "Sucesso", f"Movimentação de {tipo} registrada com sucesso!")
            self.stock_changed.emit() # Emitir o novo sinal
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível registrar a movimentação. Verifique se a quantidade de saída não excede o estoque atual.")
