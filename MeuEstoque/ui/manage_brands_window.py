from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from MeuEstoque.database.database_manager import DatabaseManager

class ManageBrandsWindow(QWidget):
    brands_changed = pyqtSignal()

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.current_brand_id = None

        self.setStyleSheet(open("MeuEstoque/ui/styles.qss").read())

        self._setup_ui()
        self._load_brands()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Título do Módulo
        title_label = QLabel("<h2>Gerenciar Marcas</h2>")
        title_label.setObjectName("moduleTitle")
        main_layout.addWidget(title_label)

        # Layout de busca
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar marca...")
        self.search_input.textChanged.connect(self._load_brands)
        search_layout.addWidget(QLabel("Buscar:"))
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # Layout principal (lista de marcas e formulário)
        content_layout = QHBoxLayout()
        
        # Lista de marcas
        self.brands_list = QListWidget()
        self.brands_list.itemClicked.connect(self._brand_selected)
        content_layout.addWidget(self.brands_list, 1)
        
        # Formulário de marca
        form_group = QGroupBox("Detalhes da Marca")
        self.form_layout = QFormLayout(form_group)
        
        self.brand_name_input = QLineEdit()
        self.form_layout.addRow("Nome da Marca:", self.brand_name_input)
        
        content_layout.addWidget(form_group, 1)
        main_layout.addLayout(content_layout)
        
        # Botões de ação
        action_buttons = QHBoxLayout()
        
        self.add_brand_btn = QPushButton("Nova Marca")
        self.add_brand_btn.setObjectName("addBrandButton")
        self.add_brand_btn.clicked.connect(self._prepare_add_brand)
        action_buttons.addWidget(self.add_brand_btn)
        
        self.save_brand_btn = QPushButton("Salvar")
        self.save_brand_btn.setObjectName("saveButton")
        self.save_brand_btn.clicked.connect(self._save_brand)
        self.save_brand_btn.setEnabled(False)
        action_buttons.addWidget(self.save_brand_btn)
        
        self.edit_brand_btn = QPushButton("Editar")
        self.edit_brand_btn.setObjectName("editBrandButton")
        self.edit_brand_btn.clicked.connect(self._edit_brand)
        self.edit_brand_btn.setEnabled(False)
        action_buttons.addWidget(self.edit_brand_btn)
        
        self.delete_brand_btn = QPushButton("Excluir")
        self.delete_brand_btn.setObjectName("deleteBrandButton")
        self.delete_brand_btn.clicked.connect(self._delete_brand)
        self.delete_brand_btn.setEnabled(False)
        action_buttons.addWidget(self.delete_brand_btn)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setObjectName("cancelButton")
        self.cancel_btn.clicked.connect(self._cancel_edit)
        self.cancel_btn.setVisible(False)
        action_buttons.addWidget(self.cancel_btn)
        
        main_layout.addLayout(action_buttons)

    def _load_brands(self):
        search_term = self.search_input.text()
        
        # Salvar o item selecionado atualmente
        currently_selected_id = None
        selected_items = self.brands_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            currently_selected_id = item.data(Qt.ItemDataRole.UserRole)
        
        # Limpar a lista
        self.brands_list.clear()
        
        # Carregar marcas do banco de dados
        brands = self.db.get_marcas()
        filtered_brands = [brand for brand in brands if search_term.lower() in brand[1].lower()]
        
        for brand in filtered_brands:
            brand_id, brand_name = brand
            item = QListWidgetItem(brand_name)
            item.setData(Qt.ItemDataRole.UserRole, brand_id)
            self.brands_list.addItem(item)
            
            # Re-selecionar o item que estava selecionado anteriormente
            if currently_selected_id is not None and brand_id == currently_selected_id:
                self.brands_list.setCurrentItem(item)
        
        # Verificar se há itens selecionados e atualizar estado dos botões
        is_item_selected = len(self.brands_list.selectedItems()) > 0
        self.edit_brand_btn.setEnabled(is_item_selected)
        self.delete_brand_btn.setEnabled(is_item_selected)

    def _brand_selected(self, item):
        brand_id = item.data(Qt.ItemDataRole.UserRole)
        brand_name = item.text()
        
        self.current_brand_id = brand_id
        self.brand_name_input.setText(brand_name)
        
        self.edit_brand_btn.setEnabled(True)
        self.delete_brand_btn.setEnabled(True)
        self.save_brand_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        self.add_brand_btn.setEnabled(True)
        self.brand_name_input.setReadOnly(True)

    def _toggle_action_buttons(self):
        is_item_selected = len(self.brands_list.selectedItems()) > 0
        self.edit_brand_btn.setEnabled(is_item_selected)
        self.delete_brand_btn.setEnabled(is_item_selected)
        
        # CORREÇÃO: Removida a chamada recursiva para _clear_form
        # A limpeza do formulário deve ser chamada explicitamente quando necessário

    def _prepare_add_brand(self):
        self._cancel_edit()  # Limpar qualquer edição em andamento
        self.current_brand_id = None
        self.brand_name_input.clear()
        self.brand_name_input.setReadOnly(False)
        self.brand_name_input.setFocus()
        
        self.save_brand_btn.setEnabled(True)
        self.cancel_btn.setVisible(True)
        self.edit_brand_btn.setEnabled(False)
        self.delete_brand_btn.setEnabled(False)
        self.add_brand_btn.setEnabled(False)

    def _edit_brand(self):
        selected_items = self.brands_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Atenção", "Selecione uma marca para editar.")
            return
        
        item = selected_items[0]
        self.current_brand_id = item.data(Qt.ItemDataRole.UserRole)
        self.brand_name_input.setText(item.text())
        self.brand_name_input.setReadOnly(False)
        self.brand_name_input.setFocus()
        
        self.save_brand_btn.setEnabled(True)
        self.cancel_btn.setVisible(True)
        self.add_brand_btn.setEnabled(False)

    def _save_brand(self):
        brand_name = self.brand_name_input.text().strip()
        if not brand_name:
            QMessageBox.warning(self, "Atenção", "O nome da marca não pode estar vazio.")
            return
        
        if self.current_brand_id is None:
            # Adicionando nova marca
            if self.db.add_marca(brand_name):
                QMessageBox.information(self, "Sucesso", f"Marca '{brand_name}' adicionada com sucesso!")
                self._cancel_edit()
                self._load_brands()
            else:
                QMessageBox.critical(self, "Erro", f"Não foi possível adicionar a marca '{brand_name}'.")
        else:
            # Atualizando marca existente
            if self.db.update_marca(self.current_brand_id, brand_name):
                QMessageBox.information(self, "Sucesso", f"Marca atualizada com sucesso para '{brand_name}'!")
                self._cancel_edit()
                self._load_brands()
            else:
                QMessageBox.critical(self, "Erro", f"Não foi possível atualizar a marca.")

    def _delete_brand(self):
        try:
            selected_items = self.brands_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Atenção", "Selecione uma marca para excluir.")
                return
            
            item = selected_items[0]
            brand_id = item.data(Qt.ItemDataRole.UserRole)
            brand_name = item.text()
            
            # Verificar se a marca está em uso por algum produto
            if self.db.marca_has_products(brand_id):
                reply = QMessageBox.question(
                    self, "Atenção",
                    f"A marca '{brand_name}' está associada a produtos. Se você excluí-la, "
                    f"esses produtos ficarão sem marca.\n\n"
                    f"Deseja continuar mesmo assim?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            else:
                reply = QMessageBox.question(
                    self, "Confirmar Exclusão",
                    f"Tem certeza que deseja excluir a marca '{brand_name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            if self.db.delete_marca(brand_id):
                QMessageBox.information(self, "Sucesso", f"Marca '{brand_name}' excluída com sucesso!")
                self._cancel_edit()
                self._load_brands()
            else:
                QMessageBox.critical(self, "Erro", f"Não foi possível excluir a marca '{brand_name}'.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao excluir a marca: {str(e)}")

    def _cancel_edit(self):
        self.brand_name_input.clear()
        self.brand_name_input.setReadOnly(True)
        self.current_brand_id = None
        
        self.save_brand_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        self.add_brand_btn.setEnabled(True)
        
        # Atualizar estado dos botões de editar e excluir com base na seleção atual
        selected_items = self.brands_list.selectedItems()
        is_item_selected = len(selected_items) > 0
        self.edit_brand_btn.setEnabled(is_item_selected)
        self.delete_brand_btn.setEnabled(is_item_selected)
        
        if is_item_selected:
            item = selected_items[0]
            self.brand_name_input.setText(item.text())
