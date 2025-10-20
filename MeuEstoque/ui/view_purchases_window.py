from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from MeuEstoque.database.database_manager import DatabaseManager
from MeuEstoque.ui.add_purchase_window import AddPurchaseWindow

class ViewPurchasesWindow(QWidget): # Alterado para QWidget
    purchase_changed = pyqtSignal()

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager

        self.setStyleSheet(open("MeuEstoque/ui/styles.qss").read())

        self._setup_ui()
        self._load_purchases()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # Remover margens para melhor integração no QStackedWidget

        # Título do Módulo
        title_label = QLabel("<h2>Gerenciar Compras</h2>")
        title_label.setObjectName("moduleTitle")
        main_layout.addWidget(title_label)

        # Layout de busca
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar compra por fornecedor ou data...")
        self.search_input.textChanged.connect(self._load_purchases)
        search_layout.addWidget(QLabel("Buscar:"))
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # Tabela de compras
        self.purchases_table = QTableWidget()
        self.purchases_table.setColumnCount(5) # Adicionado uma coluna para Status de Pagamento
        self.purchases_table.setHorizontalHeaderLabels(["Fornecedor", "Data de Emissão", "Total Final", "Status Pagamento", "ID"])
        self.purchases_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.purchases_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.purchases_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.purchases_table.doubleClicked.connect(self._open_purchase_details)
        self.purchases_table.setColumnHidden(4, True) # Ocultar a coluna ID
        self.purchases_table.itemSelectionChanged.connect(self._toggle_action_buttons)
        main_layout.addWidget(self.purchases_table)

        # Botões de ação
        button_layout = QHBoxLayout()

        self.add_purchase_btn = QPushButton("Adicionar Nova Compra")
        self.add_purchase_btn.setObjectName("addPurchaseButton")
        self.add_purchase_btn.clicked.connect(self._open_add_purchase_window)
        button_layout.addWidget(self.add_purchase_btn)

        self.edit_purchase_btn = QPushButton("Visualizar/Editar Compra")
        self.edit_purchase_btn.setObjectName("editPurchaseButton")
        self.edit_purchase_btn.clicked.connect(self._open_purchase_details)
        self.edit_purchase_btn.setEnabled(False)
        button_layout.addWidget(self.edit_purchase_btn)

        self.delete_purchase_btn = QPushButton("Excluir Compra")
        self.delete_purchase_btn.setObjectName("deletePurchaseButton")
        self.delete_purchase_btn.clicked.connect(self._delete_selected_purchase)
        self.delete_purchase_btn.setEnabled(False)
        button_layout.addWidget(self.delete_purchase_btn)

        main_layout.addLayout(button_layout)

    def _load_purchases(self):
        search_term = self.search_input.text()
        purchases = self.db.get_compras(search_term)
        self.purchases_table.setRowCount(len(purchases))

        for row_idx, purchase in enumerate(purchases):
            purchase_id = purchase[0]
            supplier_name = purchase[1]
            issue_date = purchase[2]
            total_final = purchase[3]
            status_pagamento = purchase[4] # Novo campo

            self.purchases_table.setItem(row_idx, 0, QTableWidgetItem(supplier_name))
            self.purchases_table.setItem(row_idx, 1, QTableWidgetItem(issue_date))
            total_item = QTableWidgetItem(f"R$ {total_final:.2f}")
            total_item.setTextAlignment(int(Qt.AlignmentFlag.AlignRight) | int(Qt.AlignmentFlag.AlignVCenter))
            self.purchases_table.setItem(row_idx, 2, total_item)
            self.purchases_table.setItem(row_idx, 3, QTableWidgetItem(status_pagamento)) # Exibir status de pagamento
            
            id_item = QTableWidgetItem(str(purchase_id))
            id_item.setData(Qt.ItemDataRole.UserRole, purchase_id)
            self.purchases_table.setItem(row_idx, 4, id_item) # ID agora na coluna 4

    def _toggle_action_buttons(self):
        is_purchase_selected = self.purchases_table.currentItem() is not None
        self.edit_purchase_btn.setEnabled(is_purchase_selected)
        self.delete_purchase_btn.setEnabled(is_purchase_selected)

    def _open_add_purchase_window(self):
        add_purchase_win = AddPurchaseWindow(self.db, parent=self)
        add_purchase_win.purchase_changed.connect(self._load_purchases)
        add_purchase_win.exec()

    def _open_purchase_details(self):
        selected_items = self.purchases_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione uma compra para visualizar/editar.")
            return

        row = selected_items[0].row()
        purchase_id = self.purchases_table.item(row, 3).data(Qt.ItemDataRole.UserRole)

        if purchase_id is not None:
            details_window = AddPurchaseWindow(self.db, purchase_id=purchase_id, parent=self)
            details_window.purchase_changed.connect(self._load_purchases)
            details_window.exec()

    def _delete_selected_purchase(self):
        selected_items = self.purchases_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione uma compra para excluir.")
            return

        row = selected_items[0].row()
        purchase_id = self.purchases_table.item(row, 3).data(Qt.ItemDataRole.UserRole)
        supplier_name = self.purchases_table.item(row, 0).text()
        issue_date = self.purchases_table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a compra do fornecedor '{supplier_name}' de {issue_date}? Todas as contas a pagar e itens associados também serão excluídos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # A exclusão em cascata já está configurada no database_manager.py
                # para compras, itens_compra e contas_a_pagar.
                # Basta chamar o método delete_compra se ele existisse,
                # ou executar a exclusão da compra diretamente.
                if self.db.delete_compra(purchase_id):
                    QMessageBox.information(self, "Sucesso", "Compra excluída com sucesso!")
                    self.purchases_table.clearSelection() # Limpa a seleção
                    self._load_purchases()
                    self.purchase_changed.emit() # Emitir sinal de que as compras foram alteradas
                else:
                    QMessageBox.critical(self, "Erro", "Não foi possível excluir a compra.")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível excluir a compra: {e}")
