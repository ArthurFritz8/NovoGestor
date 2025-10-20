from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QDateEdit,
    QDoubleSpinBox, QAbstractSpinBox, QComboBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from MeuEstoque.database.database_manager import DatabaseManager

class ManageAccountsPayableWindow(QWidget): # Alterado para QWidget
    accounts_changed = pyqtSignal()

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.current_account_id = None

        self.setStyleSheet(open("MeuEstoque/ui/styles.qss").read())

        self._setup_ui()
        self._load_accounts()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # Remover margens para melhor integração no QStackedWidget

        # Título do Módulo
        title_label = QLabel("<h2>Gerenciar Contas a Pagar</h2>")
        title_label.setObjectName("moduleTitle")
        main_layout.addWidget(title_label)

        # Layout de busca
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por fornecedor, vencimento ou status...")
        self.search_input.textChanged.connect(self._load_accounts)
        search_layout.addWidget(QLabel("Buscar:"))
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # Tabela de contas a pagar
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(7)
        self.accounts_table.setHorizontalHeaderLabels(["Fornecedor", "Emissão Compra", "Vencimento", "Valor", "Valor Pago", "Status", "ID"])
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.accounts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.accounts_table.setColumnHidden(6, True)
        self.accounts_table.itemSelectionChanged.connect(self._toggle_action_buttons)
        main_layout.addWidget(self.accounts_table)

        # Diálogo de Pagamento (integrado na janela para simplicidade)
        self.payment_dialog_group = QGroupBox("Registrar Pagamento")
        payment_layout = QFormLayout(self.payment_dialog_group)

        self.payment_value_spinbox = QDoubleSpinBox()
        self.payment_value_spinbox.setMinimum(0.00)
        self.payment_value_spinbox.setMaximum(999999.99)
        self.payment_value_spinbox.setPrefix("R$ ")
        self.payment_value_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        payment_layout.addRow("Valor a Pagar:", self.payment_value_spinbox)

        self.payment_status_combo = QComboBox()
        self.payment_status_combo.addItems(["Pendente", "Parcialmente Pago", "Pago"])
        payment_layout.addRow("Status:", self.payment_status_combo)

        payment_buttons_layout = QHBoxLayout()
        self.confirm_payment_btn = QPushButton("Confirmar Pagamento")
        self.confirm_payment_btn.setObjectName("confirmPaymentButton")
        self.confirm_payment_btn.clicked.connect(self._confirm_payment)
        payment_buttons_layout.addWidget(self.confirm_payment_btn)

        self.cancel_payment_btn = QPushButton("Cancelar")
        self.cancel_payment_btn.setObjectName("cancelButton")
        self.cancel_payment_btn.clicked.connect(self._hide_payment_dialog)
        payment_buttons_layout.addWidget(self.cancel_payment_btn)

        payment_layout.addRow(payment_buttons_layout)
        main_layout.addWidget(self.payment_dialog_group)
        self.payment_dialog_group.setVisible(False)

        # Layout de botões de ação (após o diálogo de pagamento)
        action_buttons_layout = QHBoxLayout()
        self.pay_account_btn = QPushButton("Registrar Pagamento")
        self.pay_account_btn.setObjectName("payAccountButton")
        self.pay_account_btn.clicked.connect(self._open_payment_dialog)
        self.pay_account_btn.setEnabled(False)
        action_buttons_layout.addWidget(self.pay_account_btn)
        main_layout.addLayout(action_buttons_layout)

    def _load_accounts(self):
        search_term = self.search_input.text()
        accounts = self.db.get_contas_a_pagar(search_term)
        self.accounts_table.setRowCount(len(accounts))

        for row_idx, account in enumerate(accounts):
            account_id = account[0]
            supplier_name = account[1]
            purchase_issue_date = account[2]
            due_date = account[3]
            value = account[4]
            paid_value = account[5]
            status = account[6]

            self.accounts_table.setItem(row_idx, 0, QTableWidgetItem(supplier_name))
            self.accounts_table.setItem(row_idx, 1, QTableWidgetItem(purchase_issue_date))
            self.accounts_table.setItem(row_idx, 2, QTableWidgetItem(due_date))
            
            value_item = QTableWidgetItem(f"R$ {value:.2f}")
            value_item.setTextAlignment(0x0004 | 0x0080) # Usando valores inteiros diretos para AlignRight | AlignVCenter
            self.accounts_table.setItem(row_idx, 3, value_item)

            paid_value_item = QTableWidgetItem(f"R$ {paid_value:.2f}")
            paid_value_item.setTextAlignment(0x0004 | 0x0080) # Usando valores inteiros diretos para AlignRight | AlignVCenter
            self.accounts_table.setItem(row_idx, 4, paid_value_item)
            
            self.accounts_table.setItem(row_idx, 5, QTableWidgetItem(status))
            
            id_item = QTableWidgetItem(str(account_id))
            id_item.setData(Qt.ItemDataRole.UserRole, account_id)
            self.accounts_table.setItem(row_idx, 6, id_item)
        
        self.accounts_changed.emit()

    def _toggle_action_buttons(self):
        is_account_selected = self.accounts_table.currentItem() is not None
        self.pay_account_btn.setEnabled(is_account_selected)
        self._hide_payment_dialog()

    def _open_payment_dialog(self):
        selected_items = self.accounts_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione uma conta para registrar o pagamento.")
            return

        row = selected_items[0].row()
        self.current_account_id = self.accounts_table.item(row, 6).data(Qt.ItemDataRole.UserRole)
        
        value_str = self.accounts_table.item(row, 3).text().replace("R$ ", "").replace(",", ".")
        paid_value_str = self.accounts_table.item(row, 4).text().replace("R$ ", "").replace(",", ".")
        status = self.accounts_table.item(row, 5).text()

        total_value = float(value_str)
        current_paid_value = float(paid_value_str)
        remaining_to_pay = total_value - current_paid_value

        self.payment_value_spinbox.setValue(remaining_to_pay)
        self.payment_status_combo.setCurrentText(status)
        self.payment_dialog_group.setVisible(True)

    def _hide_payment_dialog(self):
        self.payment_dialog_group.setVisible(False)
        self.current_account_id = None
        self.payment_value_spinbox.setValue(0.00)
        self.payment_status_combo.setCurrentIndex(0)

    def _confirm_payment(self):
        if self.current_account_id is None:
            QMessageBox.warning(self, "Atenção", "Nenhuma conta selecionada para pagamento.")
            return

        payment_amount = self.payment_value_spinbox.value()
        new_status = self.payment_status_combo.currentText()

        if payment_amount < 0:
            QMessageBox.warning(self, "Atenção", "O valor do pagamento não pode ser negativo.")
            return

        row = self.accounts_table.currentRow()
        value_str = self.accounts_table.item(row, 3).text().replace("R$ ", "").replace(",", ".")
        paid_value_str = self.accounts_table.item(row, 4).text().replace("R$ ", "").replace(",", ".")
        
        total_value = float(value_str)
        current_paid_value = float(paid_value_str)
        
        updated_paid_value = current_paid_value + payment_amount

        # A lógica para definir new_status deve considerar a seleção do usuário no combobox
        # e o valor pago.
        if updated_paid_value >= total_value:
            final_status = "Pago"
            updated_paid_value = total_value # Garante que o valor pago não exceda o total
        elif updated_paid_value > 0:
            final_status = "Parcialmente Pago"
        else:
            final_status = "Pendente"
        
        # Se o usuário selecionou um status manualmente, ele tem precedência,
        # a menos que o pagamento total force o status para "Pago".
        if new_status != final_status and new_status != "Pago":
            final_status = new_status

        if self.db.update_conta_a_pagar_status(self.current_account_id, updated_paid_value, final_status):
            QMessageBox.information(self, "Sucesso", "Pagamento registrado e status atualizado com sucesso!")
            self._load_accounts()
            self._hide_payment_dialog()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível registrar o pagamento.")
