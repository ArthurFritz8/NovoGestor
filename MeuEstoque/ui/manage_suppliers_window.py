from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from MeuEstoque.database.database_manager import DatabaseManager

class ManageSuppliersWindow(QWidget): # Alterado para QWidget
    suppliers_changed = pyqtSignal()

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.current_supplier_id = None

        self.setStyleSheet(open("MeuEstoque/ui/styles.qss").read())

        self._setup_ui()
        self._load_suppliers()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # Remover margens para melhor integração no QStackedWidget

        # Título do Módulo
        title_label = QLabel("<h2>Gerenciar Fornecedores</h2>")
        title_label.setObjectName("moduleTitle")
        main_layout.addWidget(title_label)

        # Layout de busca
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar fornecedor por nome...")
        self.search_input.textChanged.connect(self._load_suppliers)
        search_layout.addWidget(QLabel("Buscar:"))
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # Tabela de fornecedores
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(6)
        self.suppliers_table.setHorizontalHeaderLabels(["Nome", "Contato", "Telefone", "Email", "Endereço", "ID"])
        self.suppliers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.suppliers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.suppliers_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Conectar o sinal aqui, e ele será desconectado/reconectado em _load_suppliers
        self.suppliers_table.itemSelectionChanged.connect(self._toggle_action_buttons)
        self.suppliers_table.setColumnHidden(5, True)
        main_layout.addWidget(self.suppliers_table)

        # Formulário de Fornecedor (para adicionar/editar)
        self.form_group = QGroupBox("Detalhes do Fornecedor")
        self.form_layout = QFormLayout(self.form_group)

        self.name_input = QLineEdit()
        self.contact_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()

        self.form_layout.addRow("Nome:", self.name_input)
        self.form_layout.addRow("Contato:", self.contact_input)
        self.form_layout.addRow("Telefone:", self.phone_input)
        self.form_layout.addRow("Email:", self.email_input)
        self.form_layout.addRow("Endereço:", self.address_input)

        main_layout.addWidget(self.form_group)
        self.form_group.setVisible(False)

        # Layout de botões de ação
        action_buttons_layout = QHBoxLayout()

        self.add_supplier_btn = QPushButton("Adicionar Fornecedor")
        self.add_supplier_btn.setObjectName("addSupplierButton")
        self.add_supplier_btn.clicked.connect(self._add_supplier)
        action_buttons_layout.addWidget(self.add_supplier_btn)

        self.edit_supplier_btn = QPushButton("Editar Fornecedor")
        self.edit_supplier_btn.setObjectName("editSupplierButton")
        self.edit_supplier_btn.clicked.connect(self._edit_supplier)
        self.edit_supplier_btn.setEnabled(False)
        action_buttons_layout.addWidget(self.edit_supplier_btn)

        self.delete_supplier_btn = QPushButton("Excluir Fornecedor")
        self.delete_supplier_btn.setObjectName("deleteSupplierButton")
        self.delete_supplier_btn.clicked.connect(self._delete_supplier)
        self.delete_supplier_btn.setEnabled(False)
        action_buttons_layout.addWidget(self.delete_supplier_btn)

        self.save_btn = QPushButton("Salvar")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self._save_supplier)
        self.save_btn.setVisible(False) # Esconder inicialmente
        action_buttons_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setObjectName("cancelButton")
        self.cancel_btn.clicked.connect(self._clear_form)
        self.cancel_btn.setVisible(False) # Esconder inicialmente
        action_buttons_layout.addWidget(self.cancel_btn)

        main_layout.addLayout(action_buttons_layout)

    def _load_suppliers(self):
        search_term = self.search_input.text()
        suppliers = self.db.get_fornecedores(search_term)
        
        # Desconectar o sinal antes de limpar e preencher a tabela
        try:
            self.suppliers_table.itemSelectionChanged.disconnect(self._toggle_action_buttons)
        except TypeError:
            pass # O sinal pode não estar conectado na primeira execução

        self.suppliers_table.setRowCount(len(suppliers))
        self.suppliers_table.clearSelection() # Limpar seleção para evitar acionar _toggle_action_buttons

        for row_idx, supplier in enumerate(suppliers):
            self.suppliers_table.setItem(row_idx, 0, QTableWidgetItem(supplier[1]))
            self.suppliers_table.setItem(row_idx, 1, QTableWidgetItem(supplier[2] if supplier[2] else 'N/A'))
            self.suppliers_table.setItem(row_idx, 2, QTableWidgetItem(supplier[3] if supplier[3] else 'N/A'))
            self.suppliers_table.setItem(row_idx, 3, QTableWidgetItem(supplier[4] if supplier[4] else 'N/A'))
            self.suppliers_table.setItem(row_idx, 4, QTableWidgetItem(supplier[5] if supplier[5] else 'N/A'))
            
            id_item = QTableWidgetItem(str(supplier[0]))
            id_item.setData(Qt.ItemDataRole.UserRole, supplier[0])
            self.suppliers_table.setItem(row_idx, 5, id_item)

        # Reconectar o sinal após preencher a tabela
        self.suppliers_table.itemSelectionChanged.connect(self._toggle_action_buttons)
        # A chamada a _toggle_action_buttons() aqui estava causando a recursão.
        # A visibilidade inicial dos botões será definida no _setup_ui ou no __init__.
        # self._toggle_action_buttons() 

    def _toggle_action_buttons(self):
        is_supplier_selected = self.suppliers_table.currentItem() is not None
        self.edit_supplier_btn.setEnabled(is_supplier_selected)
        self.delete_supplier_btn.setEnabled(is_supplier_selected)
        
        # Apenas esconde o formulário se nenhum item estiver selecionado e o formulário estiver visível.
        # A limpeza do formulário será feita pelos métodos _add_supplier, _edit_supplier, _save_supplier e _clear_form.
        if not is_supplier_selected and self.form_group.isVisible():
            self.form_group.setVisible(False)
            self.save_btn.setVisible(False)
            self.cancel_btn.setVisible(False)

    def _add_supplier(self):
        self.current_supplier_id = None
        self._clear_form()
        self.form_group.setTitle("Adicionar Novo Fornecedor")
        self.form_group.setVisible(True)
        self.save_btn.setVisible(True)
        self.cancel_btn.setVisible(True)

    def _edit_supplier(self):
        selected_items = self.suppliers_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione um fornecedor para editar.")
            return

        row = selected_items[0].row()
        self.current_supplier_id = self.suppliers_table.item(row, 5).data(Qt.ItemDataRole.UserRole)

        supplier_data = self.db.get_fornecedor_by_id(self.current_supplier_id)
        if supplier_data:
            self.name_input.setText(supplier_data[1])
            self.contact_input.setText(supplier_data[2] if supplier_data[2] else '')
            self.phone_input.setText(supplier_data[3] if supplier_data[3] else '')
            self.email_input.setText(supplier_data[4] if supplier_data[4] else '')
            self.address_input.setText(supplier_data[5] if supplier_data[5] else '')
            
            self.form_group.setTitle(f"Editar Fornecedor: {supplier_data[1]}")
            self.form_group.setVisible(True)
            self.save_btn.setVisible(True)
            self.cancel_btn.setVisible(True)
        else:
            QMessageBox.critical(self, "Erro", "Fornecedor não encontrado.")

    def _save_supplier(self):
        name = self.name_input.text().strip()
        contact = self.contact_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        address = self.address_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Atenção", "O nome do fornecedor é obrigatório.")
            return

        if self.current_supplier_id is None:
            if self.db.add_fornecedor(name, contact, phone, email, address):
                QMessageBox.information(self, "Sucesso", "Fornecedor adicionado com sucesso!")
                self._load_suppliers()
                self._clear_form()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível adicionar o fornecedor. Verifique se o nome já existe.")
        else:
            if self.db.update_fornecedor(self.current_supplier_id, name, contact, phone, email, address):
                QMessageBox.information(self, "Sucesso", "Fornecedor atualizado com sucesso!")
                self._load_suppliers()
                self._clear_form()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível atualizar o fornecedor. Verifique se o nome já existe para outro registro.")

    def _delete_supplier(self):
        try:
            selected_items = self.suppliers_table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Atenção", "Por favor, selecione um fornecedor para excluir.")
                return

            row = selected_items[0].row()
            supplier_id = self.suppliers_table.item(row, 5).data(Qt.ItemDataRole.UserRole)
            supplier_name = self.suppliers_table.item(row, 0).text()

            # Verificar se o fornecedor tem compras associadas
            if self.db.fornecedor_has_compras(supplier_id):
                reply = QMessageBox.question(
                    self, "Atenção",
                    f"O fornecedor '{supplier_name}' possui compras associadas. Excluir o fornecedor "
                    f"também excluirá todas as compras, itens de compra e contas a pagar relacionadas.\n\n"
                    f"Tem certeza que deseja continuar?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            else:
                reply = QMessageBox.question(
                    self, "Confirmar Exclusão",
                    f"Tem certeza que deseja excluir o fornecedor '{supplier_name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            # Tentar excluir o fornecedor
            if self.db.delete_fornecedor(supplier_id):
                QMessageBox.information(self, "Sucesso", f"Fornecedor '{supplier_name}' excluído com sucesso!")
                self._load_suppliers()
            else:
                QMessageBox.critical(self, "Erro", f"Não foi possível excluir o fornecedor '{supplier_name}'.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao tentar excluir o fornecedor: {str(e)}")

    def _clear_form(self):
        self.name_input.clear()
        self.contact_input.clear()
        self.phone_input.clear()
        self.email_input.clear()
        self.address_input.clear()
        self.current_supplier_id = None
        self.form_group.setVisible(False)
        self.save_btn.setVisible(False)
        self.cancel_btn.setVisible(False)
