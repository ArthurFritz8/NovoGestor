import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QMessageBox, QHeaderView, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon, QColor # Adicionado QIcon para ícones, QColor para cores
from PyQt6.QtWidgets import QApplication, QStyle # Adicionado QStyle para ícones padrão

from MeuEstoque.database.database_manager import DatabaseManager
from MeuEstoque.ui.add_product_window import AddProductWindow
from MeuEstoque.ui.move_stock_window import MoveStockWindow
from MeuEstoque.ui.manage_brands_window import ManageBrandsWindow
from MeuEstoque.ui.product_details_window import ProductDetailsWindow # Adicionado ProductDetailsWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MeuEstoque - Sistema de Gestão de Estoque")
        self.setGeometry(100, 100, 1000, 600)

        self.db = DatabaseManager()

        self.setStyleSheet(open("MeuEstoque/ui/styles.qss").read())

        self._setup_ui()
        self._load_all_data() # Carrega todos os dados na inicialização

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Layout de busca
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar produto por nome ou código...")
        self.search_input.textChanged.connect(self._load_products)
        search_layout.addWidget(QLabel("Buscar:"))
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # Tabela de produtos
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(6) # Adicionar uma coluna para Localização
        self.product_table.setHorizontalHeaderLabels(["ID", "Nome do Produto", "Código", "Marca", "Quantidade Atual", "Localização"])
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.product_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.product_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Não permitir edição direta
        self.product_table.doubleClicked.connect(self._show_product_details) # Adicionado double click para detalhes
        self.product_table.horizontalHeader().sectionClicked.connect(self._sort_products_table) # Conectar para ordenação
        main_layout.addWidget(self.product_table)

        # Layout de botões
        button_layout = QHBoxLayout()
        
        # Adicionar Produto
        self.add_product_btn = QPushButton("Adicionar Produto")
        self.add_product_btn.setObjectName("addProductButton")
        self.add_product_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)) # Ícone de "mais"
        self.add_product_btn.clicked.connect(self._open_add_product_window)
        button_layout.addWidget(self.add_product_btn)

        # Registrar Entrada/Saída
        self.move_stock_btn = QPushButton("Registrar Entrada/Saída")
        self.move_stock_btn.setObjectName("moveStockButton")
        self.move_stock_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp)) # Ícone de setas de troca (usando SP_ArrowUp como substituto)
        self.move_stock_btn.clicked.connect(self._open_move_stock_window)
        button_layout.addWidget(self.move_stock_btn)

        # Gerenciar Marcas
        self.manage_brands_btn = QPushButton("Gerenciar Marcas")
        self.manage_brands_btn.setObjectName("manageBrandsButton")
        self.manage_brands_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)) # Ícone de engrenagem (usando SP_ComputerIcon como substituto)
        self.manage_brands_btn.clicked.connect(self._open_manage_brands_window)
        button_layout.addWidget(self.manage_brands_btn)

        # Editar Produto
        self.edit_product_btn = QPushButton("Editar Produto")
        self.edit_product_btn.setObjectName("editProductButton")
        self.edit_product_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)) # Ícone de edição (usando SP_FileDialogDetailedView como substituto)
        self.edit_product_btn.clicked.connect(self._open_edit_product_window)
        self.edit_product_btn.setEnabled(False)
        button_layout.addWidget(self.edit_product_btn)

        # Excluir Produto
        self.delete_product_btn = QPushButton("Excluir Produto")
        self.delete_product_btn.setObjectName("deleteProductButton")
        self.delete_product_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)) # Ícone de lixeira
        self.delete_product_btn.clicked.connect(self._delete_selected_product)
        self.delete_product_btn.setEnabled(False)
        button_layout.addWidget(self.delete_product_btn)
        
        self.product_table.itemSelectionChanged.connect(self._toggle_action_buttons)
        
        main_layout.addLayout(button_layout)

        # Dashboard de Estatísticas
        dashboard_group = QGroupBox("Estatísticas do Estoque")
        dashboard_layout = QHBoxLayout(dashboard_group)

        self.total_products_label = QLabel("Total de Produtos: 0")
        self.low_stock_label = QLabel("Estoque Baixo: 0")
        self.total_brands_label = QLabel("Total de Marcas: 0")

        dashboard_layout.addWidget(self.total_products_label)
        dashboard_layout.addWidget(self.low_stock_label)
        dashboard_layout.addWidget(self.total_brands_label)
        main_layout.addWidget(dashboard_group)

    def _load_all_data(self):
        self._load_products()
        self._load_dashboard_stats()

    def _load_products(self):
        search_term = self.search_input.text()
        products = self.db.get_produtos(search_term)
        self.product_table.setRowCount(len(products))
        self.product_table.setSortingEnabled(False) # Desabilitar temporariamente a ordenação para preencher a tabela

        low_stock_threshold = 5 # Limite para estoque baixo
        for row_idx, product in enumerate(products):
            # product agora tem 7 elementos: id, nome_produto, codigo_produto, nome_marca, quantidade_atual, descricao, localizacao
            product_id = product[0]
            product_name = product[1]
            product_code = product[2] if product[2] else 'N/A'
            brand_name = product[3] if product[3] else 'Sem Marca'
            quantity = product[4]
            location = product[6] if product[6] else 'N/A'

            id_item = QTableWidgetItem(str(product_id))
            name_item = QTableWidgetItem(product_name)
            code_item = QTableWidgetItem(product_code)
            brand_item = QTableWidgetItem(brand_name)
            quantity_item = QTableWidgetItem(str(quantity))
            location_item = QTableWidgetItem(location)

            # Alinhar texto à direita para colunas numéricas
            quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            self.product_table.setItem(row_idx, 0, id_item) # ID
            self.product_table.setItem(row_idx, 1, name_item) # Nome do Produto
            self.product_table.setItem(row_idx, 2, code_item) # Código
            self.product_table.setItem(row_idx, 3, brand_item) # Marca
            self.product_table.setItem(row_idx, 4, quantity_item) # Quantidade Atual
            self.product_table.setItem(row_idx, 5, location_item) # Localização

            # Aplicar estilo de estoque baixo
            if quantity <= low_stock_threshold:
                for col in range(self.product_table.columnCount()):
                    item = self.product_table.item(row_idx, col)
                    if item:
                        item.setData(Qt.ItemDataRole.WhatsThisRole, "low-stock") # Usar WhatsThisRole para identificar o estilo
            
            # Configurar cores de linha alternadas (efeito zebrado)
            if row_idx % 2 == 0:
                for col in range(self.product_table.columnCount()):
                    item = self.product_table.item(row_idx, col)
                    if item:
                        item.setData(Qt.ItemDataRole.BackgroundRole, QColor("#f8f9fa")) # Cor para linhas pares
            else:
                for col in range(self.product_table.columnCount()):
                    item = self.product_table.item(row_idx, col)
                    if item:
                        item.setData(Qt.ItemDataRole.BackgroundRole, QColor("white")) # Cor para linhas ímpares

        self.product_table.setSortingEnabled(True) # Reabilitar ordenação
        self.current_sort_column = -1
        self.current_sort_order = Qt.SortOrder.AscendingOrder

    def _sort_products_table(self, logical_index):
        if logical_index == self.current_sort_column:
            self.current_sort_order = (
                Qt.SortOrder.DescendingOrder
                if self.current_sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )
        else:
            self.current_sort_column = logical_index
            self.current_sort_order = Qt.SortOrder.AscendingOrder

        self.product_table.sortItems(self.current_sort_column, self.current_sort_order)

    def _show_product_details(self, index):
        row = index.row()
        product_id = int(self.product_table.item(row, 0).text())
        
        details_window = ProductDetailsWindow(self.db, product_id, self)
        details_window.exec()

    def _load_dashboard_stats(self):
        total_products = self.db.get_total_products_count()
        low_stock_products = self.db.get_low_stock_products_count()
        total_brands = self.db.get_total_brands_count()

        self.total_products_label.setText(f"Total de Produtos: {total_products}")
        self.low_stock_label.setText(f"Estoque Baixo: {low_stock_products}")
        self.total_brands_label.setText(f"Total de Marcas: {total_brands}")

    def _open_add_product_window(self):
        self.add_product_win = AddProductWindow(self.db, parent=self)
        self.add_product_win.product_changed.connect(self._load_all_data) # Conectar ao novo sinal
        self.add_product_win.exec()

    def _open_edit_product_window(self):
        selected_items = self.product_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione um produto para editar.")
            return
        row = selected_items[0].row()
        product_id = int(self.product_table.item(row, 0).text())
        
        self.edit_product_win = AddProductWindow(self.db, product_id=product_id, parent=self)
        self.edit_product_win.product_changed.connect(self._load_all_data) # Conectar ao novo sinal
        self.edit_product_win.exec()

    def _open_move_stock_window(self):
        self.move_stock_win = MoveStockWindow(self.db, parent=self)
        self.move_stock_win.stock_changed.connect(self._load_all_data) # Conectar ao novo sinal
        self.move_stock_win.exec()

    def _open_manage_brands_window(self):
        self.manage_brands_win = ManageBrandsWindow(self.db, parent=self)
        self.manage_brands_win.brands_changed.connect(self._load_all_data) # Conectar ao novo sinal
        self.manage_brands_win.exec()

    def _toggle_action_buttons(self):
        is_product_selected = self.product_table.currentItem() is not None
        self.delete_product_btn.setEnabled(is_product_selected)
        self.edit_product_btn.setEnabled(is_product_selected) # Habilitar/desabilitar botão de edição

    def _delete_selected_product(self):
        selected_items = self.product_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione um produto para excluir.")
            return

        row = selected_items[0].row()
        product_id = int(self.product_table.item(row, 0).text())
        product_name = self.product_table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o produto '{product_name}'? Todas as movimentações associadas também serão excluídas.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_produto(product_id):
                QMessageBox.information(self, "Sucesso", f"Produto '{product_name}' excluído com sucesso!")
                self._load_all_data() # Recarregar todos os dados após a exclusão
            else:
                QMessageBox.critical(self, "Erro", f"Não foi possível excluir o produto '{product_name}'.")

    def closeEvent(self, event):
        self.db.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
