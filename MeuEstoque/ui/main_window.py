import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QMessageBox, QHeaderView, QGroupBox, QListWidget, QListWidgetItem, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon, QColor
from PyQt6.QtWidgets import QApplication, QStyle

from MeuEstoque.database.database_manager import DatabaseManager
from MeuEstoque.ui.add_product_window import AddProductWindow
from MeuEstoque.ui.move_stock_window import MoveStockWindow
from MeuEstoque.ui.manage_brands_window import ManageBrandsWindow
from MeuEstoque.ui.product_details_window import ProductDetailsWindow
from MeuEstoque.ui.manage_suppliers_window import ManageSuppliersWindow
from MeuEstoque.ui.view_purchases_window import ViewPurchasesWindow
from MeuEstoque.ui.manage_accounts_payable_window import ManageAccountsPayableWindow

# Importar as classes das janelas que serão convertidas em widgets
# Por enquanto, vamos manter as janelas como estão e adaptá-las para serem usadas como widgets
# Isso será feito em etapas posteriores.

class ProductsWidget(QWidget):
    product_changed = pyqtSignal() # Sinal para notificar a janela principal sobre mudanças
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self._setup_ui()
        self._load_all_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Layout de busca
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar produto por nome ou código...")
        self.search_input.textChanged.connect(self._load_products_data) # Conectar ao método correto
        search_layout.addWidget(QLabel("Buscar:"))
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # Tabela de produtos
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(5)
        self.product_table.setHorizontalHeaderLabels(["Nome do Produto", "Código", "Marca", "Quantidade Atual", "Localização"])
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.product_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.product_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.product_table.doubleClicked.connect(self._show_product_details)
        self.product_table.horizontalHeader().sectionClicked.connect(self._sort_products_table)
        main_layout.addWidget(self.product_table)

        # Layout de botões
        button_layout = QHBoxLayout()
        
        self.add_product_btn = QPushButton("Adicionar Produto")
        self.add_product_btn.setObjectName("addProductButton")
        self.add_product_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        self.add_product_btn.clicked.connect(self._open_add_product_window)
        button_layout.addWidget(self.add_product_btn)

        self.move_stock_btn = QPushButton("Registrar Entrada/Saída")
        self.move_stock_btn.setObjectName("moveStockButton")
        self.move_stock_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp))
        self.move_stock_btn.clicked.connect(self._open_move_stock_window)
        button_layout.addWidget(self.move_stock_btn)

        self.edit_product_btn = QPushButton("Editar Produto")
        self.edit_product_btn.setObjectName("editProductButton")
        self.edit_product_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.edit_product_btn.clicked.connect(self._open_edit_product_window)
        self.edit_product_btn.setEnabled(False)
        button_layout.addWidget(self.edit_product_btn)

        self.delete_product_btn = QPushButton("Excluir Produto")
        self.delete_product_btn.setObjectName("deleteProductButton")
        self.delete_product_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
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
        self._load_products_data()
        self._load_dashboard_stats()

    def _load_products_data(self):
        search_term = self.search_input.text()
        products = self.db.get_produtos(search_term)
        self.product_table.setRowCount(len(products))
        self.product_table.clearSelection()

        for row_idx, product in enumerate(products):
            p_id, p_name, p_code, p_brand, p_qty, p_desc, p_location = product
            
            item_name = QTableWidgetItem(p_name)
            item_name.setData(Qt.ItemDataRole.UserRole, p_id) # Armazenar o ID do produto
            self.product_table.setItem(row_idx, 0, item_name)
            self.product_table.setItem(row_idx, 1, QTableWidgetItem(p_code if p_code else 'N/A'))
            self.product_table.setItem(row_idx, 2, QTableWidgetItem(p_brand if p_brand else 'N/A'))
            self.product_table.setItem(row_idx, 3, QTableWidgetItem(str(p_qty)))
            self.product_table.setItem(row_idx, 4, QTableWidgetItem(p_location if p_location else 'N/A'))

        self._toggle_action_buttons() # Atualizar estado dos botões após carregar os dados

    def _sort_products_table(self, logical_index):
        # Inicializar current_sort_column e current_sort_order se não existirem
        if not hasattr(self, 'current_sort_column'):
            self.current_sort_column = -1
            self.current_sort_order = Qt.SortOrder.AscendingOrder

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
        product_id = self.product_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if product_id is not None:
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
        self.add_product_win.product_changed.connect(self._load_all_data)
        self.add_product_win.exec()

    def _open_edit_product_window(self):
        selected_items = self.product_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione um produto para editar.")
            return
        row = selected_items[0].row()
        product_id = self.product_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if product_id is not None:
            self.edit_product_win = AddProductWindow(self.db, product_id=product_id, parent=self)
            self.edit_product_win.product_changed.connect(self._load_all_data)
            self.edit_product_win.exec()

    def _open_move_stock_window(self):
        self.move_stock_win = MoveStockWindow(self.db, parent=self)
        self.move_stock_win.stock_changed.connect(self._load_all_data)
        self.move_stock_win.exec()

    def _toggle_action_buttons(self):
        is_product_selected = self.product_table.currentItem() is not None
        self.delete_product_btn.setEnabled(is_product_selected)
        self.edit_product_btn.setEnabled(is_product_selected)

    def _delete_selected_product(self):
        selected_items = self.product_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione um produto para excluir.")
            return

        row = selected_items[0].row()
        product_id = self.product_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        product_name = self.product_table.item(row, 0).text()

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o produto '{product_name}'? Todas as movimentações associadas também serão excluídas.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.db.delete_produto(product_id):
                    QMessageBox.information(self, "Sucesso", f"Produto '{product_name}' excluído com sucesso!")
                    self.product_table.clearSelection() # Limpa a seleção
                    self._load_all_data() # Recarrega os dados
                else:
                    QMessageBox.critical(self, "Erro", f"Não foi possível excluir o produto '{product_name}'.")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao excluir o produto: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MeuEstoque - Sistema de Gestão de Estoque")
        self.setGeometry(100, 100, 1200, 700) # Aumentar o tamanho da janela principal

        self.db = DatabaseManager()

        self.setStyleSheet(open("MeuEstoque/ui/styles.qss").read())

        self._setup_ui()
        # self._load_all_data() # Não é mais necessário aqui, cada widget carregará seus próprios dados

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget) # Layout principal horizontal

        # Menu Lateral
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setObjectName("sidebar")
        
        # Itens do menu
        self.sidebar.addItem(QListWidgetItem(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)), "Produtos"))
        self.sidebar.addItem(QListWidgetItem(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)), "Marcas"))
        self.sidebar.addItem(QListWidgetItem(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)), "Fornecedores"))
        self.sidebar.addItem(QListWidgetItem(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)), "Compras"))
        self.sidebar.addItem(QListWidgetItem(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogYesButton)), "Contas a Pagar"))
        
        self.sidebar.currentRowChanged.connect(self._change_page)
        main_layout.addWidget(self.sidebar)

        # Área de Conteúdo Principal (Stacked Widget)
        self.content_area = QStackedWidget()
        main_layout.addWidget(self.content_area)

        # Adicionar os widgets para cada módulo
        self.products_widget = ProductsWidget(self.db, self)
        self.content_area.addWidget(self.products_widget)

        # As outras janelas (Marcas, Fornecedores, Compras, Contas a Pagar) precisarão ser convertidas em QWidgets
        # Por enquanto, vamos adicionar placeholders ou instâncias das janelas existentes (se forem QDialogs, elas se comportarão como modais)
        # Para Marcas, Fornecedores, Compras e Contas a Pagar, vamos instanciar as janelas existentes como widgets
        # e garantir que elas se comportem como parte do layout, não como janelas separadas.
        # Isso exigirá que essas classes sejam modificadas para herdar de QWidget em vez de QDialog,
        # e que seus métodos de `exec()` sejam removidos ou adaptados.

        # Placeholder para Marcas (será substituído por um QWidget real)
        self.brands_widget = ManageBrandsWindow(self.db, self) # Temporariamente usando a janela como widget
        self.content_area.addWidget(self.brands_widget)

        # Placeholder para Fornecedores (será substituído por um QWidget real)
        self.suppliers_widget = ManageSuppliersWindow(self.db, self) # Temporariamente usando a janela como widget
        self.content_area.addWidget(self.suppliers_widget)

        # Placeholder para Compras (será substituído por um QWidget real)
        self.purchases_widget = ViewPurchasesWindow(self.db, self) # Temporariamente usando a janela como widget
        self.content_area.addWidget(self.purchases_widget)

        # Placeholder para Contas a Pagar (será substituído por um QWidget real)
        self.accounts_payable_widget = ManageAccountsPayableWindow(self.db, self) # Temporariamente usando a janela como widget
        self.content_area.addWidget(self.accounts_payable_widget)

        # Conectar sinais para recarregar dados quando houver mudanças
        self.products_widget.product_changed.connect(self.products_widget._load_all_data) # Recarregar produtos
        self.brands_widget.brands_changed.connect(self.brands_widget._load_brands) # Recarregar marcas
        self.suppliers_widget.suppliers_changed.connect(self.suppliers_widget._load_suppliers) # Recarregar fornecedores
        self.purchases_widget.purchase_changed.connect(self.purchases_widget._load_purchases) # Recarregar compras
        self.accounts_payable_widget.accounts_changed.connect(self.accounts_payable_widget._load_accounts) # Reativado

        # Definir a página inicial
        self.sidebar.setCurrentRow(0)

    def _change_page(self, index):
        self.content_area.setCurrentIndex(index)

    def closeEvent(self, event):
        self.db.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
