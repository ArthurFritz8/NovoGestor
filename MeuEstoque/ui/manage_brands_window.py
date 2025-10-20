import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import pyqtSignal

from MeuEstoque.database.database_manager import DatabaseManager

class ManageBrandsWindow(QDialog):
    brands_changed = pyqtSignal() # Sinal renomeado para indicar alteração nas marcas

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciar Marcas")
        self.setGeometry(250, 250, 350, 400)
        self.db = db_manager
        self.setStyleSheet(open("MeuEstoque/ui/styles.qss").read())
        self._setup_ui()
        self._load_brands()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Adicionar Nova Marca
        add_brand_layout = QHBoxLayout()
        add_brand_layout.addWidget(QLabel("Nova Marca:"))
        self.new_brand_input = QLineEdit()
        add_brand_layout.addWidget(self.new_brand_input)
        self.add_brand_btn = QPushButton("Adicionar")
        self.add_brand_btn.clicked.connect(self._add_brand)
        add_brand_layout.addWidget(self.add_brand_btn)
        main_layout.addLayout(add_brand_layout)

        # Lista de Marcas
        main_layout.addWidget(QLabel("Marcas Cadastradas:"))
        self.brand_list_widget = QListWidget()
        main_layout.addWidget(self.brand_list_widget)

        # Botão Excluir Marca
        self.delete_brand_btn = QPushButton("Excluir Marca Selecionada")
        self.delete_brand_btn.clicked.connect(self._delete_brand)
        self.delete_brand_btn.setEnabled(False) # Desabilitado inicialmente
        self.brand_list_widget.itemSelectionChanged.connect(self._toggle_delete_button)
        self.brand_list_widget.itemClicked.connect(self._on_brand_item_clicked)
        main_layout.addWidget(self.delete_brand_btn)

        # Botão Fechar
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)

    def _load_brands(self):
        self.brand_list_widget.clear()
        self.brands_data = self.db.get_marcas()
        for brand_id, brand_name in self.brands_data:
            item = QListWidgetItem(brand_name)
            item.setData(1, brand_id) # Armazena o ID no UserRole
            self.brand_list_widget.addItem(item)

    def _add_brand(self):
        brand_name = self.new_brand_input.text().strip()
        if not brand_name:
            QMessageBox.warning(self, "Erro de Validação", "O nome da marca não pode ser vazio.")
            return
        
        if self.db.add_marca(brand_name):
            QMessageBox.information(self, "Sucesso", f"Marca '{brand_name}' adicionada com sucesso!")
            self.new_brand_input.clear()
            self._load_brands()
            self.brands_changed.emit() # Emitir o novo sinal
        else:
            QMessageBox.critical(self, "Erro", f"Não foi possível adicionar a marca '{brand_name}'. Talvez ela já exista.")

    def _on_brand_item_clicked(self, item):
        self.new_brand_input.setText(item.text())

    def _toggle_delete_button(self):
        self.delete_brand_btn.setEnabled(self.brand_list_widget.currentItem() is not None)

    def _delete_brand(self):
        selected_item = self.brand_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione uma marca para excluir.")
            return

        brand_id = selected_item.data(1)
        brand_name = selected_item.text()

        if self.db.marca_has_products(brand_id):
            QMessageBox.critical(self, "Erro", f"Não é possível excluir a marca '{brand_name}' porque há produtos associados a ela.")
            return

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a marca '{brand_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_marca(brand_id):
                QMessageBox.information(self, "Sucesso", f"Marca '{brand_name}' excluída com sucesso!")
                self._load_brands()
                self.brands_changed.emit() # Emitir o novo sinal
            else:
                QMessageBox.critical(self, "Erro", f"Não foi possível excluir a marca '{brand_name}'.")
