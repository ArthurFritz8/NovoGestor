from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QDateEdit, QDoubleSpinBox, QAbstractSpinBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from MeuEstoque.database.database_manager import DatabaseManager

class AddPurchaseWindow(QDialog):
    purchase_changed = pyqtSignal() # Sinal para notificar a janela principal sobre mudanças

    def __init__(self, db_manager, purchase_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar/Editar Compra")
        self.setGeometry(150, 150, 1000, 700)
        self.db = db_manager
        self.purchase_id = purchase_id
        self.products_in_purchase = {} # {product_id: {'nome': name, 'quantidade': qty, 'preco_unitario': price}}

        self.setStyleSheet(open("MeuEstoque/ui/styles.qss").read())

        self._setup_ui()
        self._load_suppliers_to_combobox()
        self._load_products_to_combobox()

        if self.purchase_id:
            self._load_purchase_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Formulário de detalhes da compra
        form_layout = QFormLayout()

        self.supplier_combo = QComboBox()
        form_layout.addRow("Fornecedor:", self.supplier_combo)

        self.issue_date_edit = QDateEdit(calendarPopup=True)
        self.issue_date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Data de Emissão:", self.issue_date_edit)

        self.delivery_date_edit = QDateEdit(calendarPopup=True)
        self.delivery_date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Data de Entrega:", self.delivery_date_edit)

        self.due_date_input = QLineEdit() # Prazo de entrega como texto
        self.due_date_input.setPlaceholderText("Ex: 30 dias, 1 semana")
        form_layout.addRow("Prazo de Entrega:", self.due_date_input)

        self.observation_input = QLineEdit()
        form_layout.addRow("Observação:", self.observation_input)

        main_layout.addLayout(form_layout)

        # Seção de Itens da Compra
        items_group_layout = QVBoxLayout()
        items_group_layout.addWidget(QLabel("<h3>Itens da Compra</h3>"))

        # Adicionar item
        add_item_layout = QHBoxLayout()
        self.product_combo = QComboBox()
        add_item_layout.addWidget(QLabel("Produto:"))
        add_item_layout.addWidget(self.product_combo)

        self.quantity_spinbox = QDoubleSpinBox()
        self.quantity_spinbox.setMinimum(1.00) # Alterado para 1.00
        self.quantity_spinbox.setMaximum(999999.99)
        self.quantity_spinbox.setValue(1.00) # Valor padrão 1.00
        self.quantity_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        add_item_layout.addWidget(QLabel("Quantidade:"))
        add_item_layout.addWidget(self.quantity_spinbox)

        self.unit_price_spinbox = QDoubleSpinBox()
        self.unit_price_spinbox.setMinimum(1.00) # Alterado para 1.00
        self.unit_price_spinbox.setMaximum(999999.99)
        self.unit_price_spinbox.setValue(1.00) # Valor padrão 1.00
        self.unit_price_spinbox.setPrefix("R$ ")
        self.unit_price_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        add_item_layout.addWidget(QLabel("Preço Unitário:"))
        add_item_layout.addWidget(self.unit_price_spinbox)

        self.add_item_btn = QPushButton("Adicionar Item")
        self.add_item_btn.clicked.connect(self._add_product_to_purchase)
        add_item_layout.addWidget(self.add_item_btn)
        items_group_layout.addLayout(add_item_layout)

        # Tabela de itens da compra
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Produto", "Quantidade", "Preço Unitário", "Total"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        items_group_layout.addWidget(self.items_table)

        main_layout.addLayout(items_group_layout)

        # Totais da Compra
        totals_layout = QFormLayout()
        self.subtotal_label = QLabel("R$ 0.00")
        totals_layout.addRow("Subtotal:", self.subtotal_label)

        self.discount_spinbox = QDoubleSpinBox()
        self.discount_spinbox.setMinimum(0.00)
        self.discount_spinbox.setMaximum(999999.99)
        self.discount_spinbox.setPrefix("R$ ")
        self.discount_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.discount_spinbox.valueChanged.connect(self._calculate_totals)
        totals_layout.addRow("Desconto:", self.discount_spinbox)

        self.freight_spinbox = QDoubleSpinBox()
        self.freight_spinbox.setMinimum(0.00)
        self.freight_spinbox.setMaximum(999999.99)
        self.freight_spinbox.setPrefix("R$ ")
        self.freight_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.freight_spinbox.valueChanged.connect(self._calculate_totals)
        totals_layout.addRow("Frete:", self.freight_spinbox)

        self.total_final_label = QLabel("R$ 0.00")
        totals_layout.addRow("Total Final:", self.total_final_label)
        main_layout.addLayout(totals_layout)

        # Botões de ação
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Salvar Compra")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self._save_purchase)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setObjectName("cancelButton")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(button_layout)

    def _load_suppliers_to_combobox(self):
        self.supplier_combo.clear()
        self.supplier_combo.addItem("Selecione um Fornecedor", None)
        suppliers = self.db.get_all_fornecedores_for_combobox()
        for supplier_id, supplier_name in suppliers:
            self.supplier_combo.addItem(supplier_name, supplier_id)

    def _load_products_to_combobox(self):
        self.product_combo.clear()
        self.product_combo.addItem("Selecione um Produto", None)
        products = self.db.get_all_products_for_combobox()
        for product_id, product_name, product_code in products:
            display_text = f"{product_name} ({product_code})" if product_code else product_name
            self.product_combo.addItem(display_text, product_id)

    def _add_product_to_purchase(self):
        product_id = self.product_combo.currentData()
        quantity = self.quantity_spinbox.value()
        unit_price = self.unit_price_spinbox.value()

        if product_id is None:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione um produto.")
            return
        if quantity <= 0:
            QMessageBox.warning(self, "Atenção", "A quantidade deve ser maior que zero.")
            return
        if unit_price <= 0:
            QMessageBox.warning(self, "Atenção", "O preço unitário deve ser maior que zero.")
            return

        product_name = self.product_combo.currentText().split('(')[0].strip() # Pega só o nome do produto

        # Adiciona ou atualiza o produto na lista
        self.products_in_purchase[product_id] = {
            'nome': product_name,
            'quantidade': quantity,
            'preco_unitario': unit_price
        }
        self._update_items_table()
        self._calculate_totals()
        self.quantity_spinbox.setValue(0.01)
        self.unit_price_spinbox.setValue(0.01)
        self.product_combo.setCurrentIndex(0)

    def _update_items_table(self):
        self.items_table.setRowCount(len(self.products_in_purchase))
        row = 0
        for product_id, data in self.products_in_purchase.items():
            total_item = data['quantidade'] * data['preco_unitario']
            self.items_table.setItem(row, 0, QTableWidgetItem(data['nome']))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(data['quantidade'])))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"R$ {data['preco_unitario']:.2f}"))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"R$ {total_item:.2f}"))
            row += 1

    def _calculate_totals(self):
        subtotal = sum(data['quantidade'] * data['preco_unitario'] for data in self.products_in_purchase.values())
        discount = self.discount_spinbox.value()
        freight = self.freight_spinbox.value()

        total_final = subtotal - discount + freight
        if total_final < 0: # Evitar total negativo
            total_final = 0.0

        self.subtotal_label.setText(f"R$ {subtotal:.2f}")
        self.total_final_label.setText(f"R$ {total_final:.2f}")

    def _load_purchase_data(self):
        purchase_data, items_data = self.db.get_compra_details(self.purchase_id)
        if purchase_data:
            # purchase_data: id, f.nome, data_emissao, data_entrega, prazo_entrega, subtotal, desconto, frete, total_final, observacao, status_pagamento
            supplier_name = purchase_data[1]
            index = self.supplier_combo.findText(supplier_name)
            if index != -1:
                self.supplier_combo.setCurrentIndex(index)
            
            self.issue_date_edit.setDate(QDate.fromString(purchase_data[2].split(" ")[0], Qt.DateFormat.ISODate)) # Ajustar formato
            self.delivery_date_edit.setDate(QDate.fromString(purchase_data[3].split(" ")[0], Qt.DateFormat.ISODate)) # Ajustar formato
            self.due_date_input.setText(purchase_data[4] if purchase_data[4] else '')
            self.observation_input.setText(purchase_data[9] if purchase_data[9] else '')
            self.discount_spinbox.setValue(purchase_data[6])
            self.freight_spinbox.setValue(purchase_data[7])
            self.current_status_pagamento = purchase_data[10] # Armazenar o status de pagamento atual

            # Carregar itens da compra
            self.products_in_purchase = {} # Limpar para recarregar
            for item in items_data:
                # item: ic.produto_id, p.nome_produto, ic.quantidade, ic.preco_unitario
                product_id = item[0]
                product_name = item[1]
                quantity = item[2]
                unit_price = item[3]
                
                self.products_in_purchase[product_id] = {
                    'nome': product_name,
                    'quantidade': quantity,
                    'preco_unitario': unit_price
                }
            self._update_items_table()
            self._calculate_totals()
            self.setWindowTitle(f"Editar Compra: {purchase_data[0]}")

            # Preencher os spinboxes com os dados do primeiro item para edição
            if items_data:
                first_item = items_data[0]
                first_product_id = first_item[0]
                first_product_name = first_item[1]
                first_quantity = first_item[2]
                first_unit_price = first_item[3]

                # Encontrar o índice do produto no combobox
                for i in range(self.product_combo.count()):
                    if self.product_combo.itemData(i) == first_product_id:
                        self.product_combo.setCurrentIndex(i)
                        break
                self.quantity_spinbox.setValue(first_quantity)
                self.unit_price_spinbox.setValue(first_unit_price)
        else:
            QMessageBox.critical(self, "Erro", "Compra não encontrada.")
            self.reject()

    def _save_purchase(self):
        supplier_id = self.supplier_combo.currentData()
        issue_date = self.issue_date_edit.date().toString(Qt.DateFormat.ISODate)
        delivery_date = self.delivery_date_edit.date().toString(Qt.DateFormat.ISODate)
        due_date = self.due_date_input.text().strip()
        observation = self.observation_input.text().strip()
        subtotal = float(self.subtotal_label.text().replace("R$ ", "").replace(",", "."))
        discount = self.discount_spinbox.value()
        freight = self.freight_spinbox.value()
        total_final = float(self.total_final_label.text().replace("R$ ", "").replace(",", "."))
        
        # Definir o status de pagamento
        if self.purchase_id is None:
            # Nova compra: status inicial é "Pendente"
            status_pagamento_final = "Pendente"
        else:
            # Edição de compra: manter o status existente
            status_pagamento_final = self.current_status_pagamento if hasattr(self, 'current_status_pagamento') else "Pendente"

        if supplier_id is None:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione um fornecedor.")
            return
        if not self.products_in_purchase:
            QMessageBox.warning(self, "Atenção", "Adicione pelo menos um item à compra.")
            return

        if self.purchase_id is None: # Nova compra
            new_purchase_id = self.db.add_compra(
                supplier_id, issue_date, delivery_date, due_date,
                subtotal, discount, freight, total_final, observation, status_pagamento_final
            )
            if new_purchase_id:
                for product_id, data in self.products_in_purchase.items():
                    if not self.db.add_item_compra(new_purchase_id, product_id, data['quantidade'], data['preco_unitario']):
                        QMessageBox.critical(self, "Erro", f"Não foi possível adicionar o item {data['nome']} à compra.")
                        # Considerar rollback da compra se um item falhar
                        return
                
                # Adicionar conta a pagar (simplificado para uma única conta com o total final)
                if not self.db.add_conta_a_pagar(new_purchase_id, delivery_date, total_final): # Usando data de entrega como vencimento
                    QMessageBox.critical(self, "Erro", "Não foi possível gerar a conta a pagar para esta compra.")
                    return

                QMessageBox.information(self, "Sucesso", "Compra adicionada com sucesso!")
                self.purchase_changed.emit()
                self.accept()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível adicionar a compra.")
        else: # Editar compra existente
            itens_para_atualizar = []
            for product_id, data in self.products_in_purchase.items():
                itens_para_atualizar.append({
                    'produto_id': product_id,
                    'quantidade': data['quantidade'],
                    'preco_unitario': data['preco_unitario']
                })

            if self.db.update_compra(
                self.purchase_id, supplier_id, issue_date, delivery_date, due_date,
                subtotal, discount, freight, total_final, observation, status_pagamento_final, itens_para_atualizar
            ):
                QMessageBox.information(self, "Sucesso", "Compra atualizada com sucesso!")
                self.purchase_changed.emit()
                self.accept()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível atualizar a compra.")
