import sys
import os
import shutil
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QSpinBox, QFormLayout, QGroupBox,
    QFileDialog, QScrollArea, QWidget, QGridLayout
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QImage

from MeuEstoque.database.database_manager import DatabaseManager

# Configurar logging para arquivo
logging.basicConfig(filename='debug.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class AddProductWindow(QDialog):
    product_added = pyqtSignal()

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Novo Produto")
        self.setGeometry(150, 150, 600, 700)
        self.db = db_manager
        self.setStyleSheet(open("MeuEstoque/ui/styles.qss").read())
        self.selected_image_paths = []
        logging.debug("AddProductWindow inicializada.")
        self._setup_ui()
        self._load_brands()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        product_details_group = QGroupBox("Detalhes do Produto")
        product_details_layout = QFormLayout(product_details_group)

        self.name_input = QLineEdit()
        product_details_layout.addRow("Nome do Produto:", self.name_input)

        self.code_input = QLineEdit()
        product_details_layout.addRow("Código do Produto (opcional):", self.code_input)

        self.desc_input = QLineEdit()
        product_details_layout.addRow("Descrição (opcional):", self.desc_input)
        
        self.brand_combobox = QComboBox()
        product_details_layout.addRow("Marca:", self.brand_combobox)
        
        main_layout.addWidget(product_details_group)

        stock_info_group = QGroupBox("Informações de Estoque")
        stock_info_layout = QFormLayout(stock_info_group)

        self.qty_spinbox = QSpinBox()
        self.qty_spinbox.setMinimum(0)
        self.qty_spinbox.setMaximum(999999)
        stock_info_layout.addRow("Quantidade Inicial:", self.qty_spinbox)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Ex: Prateleira A1, Corredor 3")
        stock_info_layout.addRow("Localização no Estoque (opcional):", self.location_input)

        main_layout.addWidget(stock_info_group)

        images_group = QGroupBox("Imagens do Produto")
        images_layout = QVBoxLayout(images_group)

        self.add_images_btn = QPushButton("Anexar Imagens")
        self.add_images_btn.clicked.connect(self._add_images)
        images_layout.addWidget(self.add_images_btn)

        self.image_preview_area = QScrollArea()
        self.image_preview_area.setWidgetResizable(True)
        self.image_preview_widget = QWidget()
        self.image_preview_layout = QGridLayout(self.image_preview_widget)
        self.image_preview_area.setWidget(self.image_preview_widget)
        images_layout.addWidget(self.image_preview_area)

        main_layout.addWidget(images_group)

        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Salvar")
        self.save_btn.clicked.connect(self._save_product)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(button_layout)

    def _load_brands(self):
        self.brand_combobox.clear()
        self.brands_data = self.db.get_marcas()
        if not self.brands_data:
            self.brand_combobox.addItem("Nenhuma marca cadastrada", -1)
            self.save_btn.setEnabled(False)
            QMessageBox.warning(self, "Atenção", "Nenhuma marca cadastrada. Por favor, cadastre uma marca antes de adicionar um produto.")
            logging.warning("Nenhuma marca cadastrada. Botão Salvar desabilitado.")
            return
        
        self.save_btn.setEnabled(True)
        for brand_id, brand_name in self.brands_data:
            self.brand_combobox.addItem(brand_name, brand_id)
        logging.debug(f"Marcas carregadas: {self.brands_data}")

    def _add_images(self):
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Selecionar Imagens do Produto")
        file_dialog.setNameFilter("Imagens (*.png *.jpg *.jpeg *.gif)")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        if file_dialog.exec() == QDialog.DialogCode.Accepted:
            new_image_paths = file_dialog.selectedFiles()
            self.selected_image_paths.extend(new_image_paths)
            self._update_image_previews()
            logging.debug(f"Imagens selecionadas: {new_image_paths}")

    def _update_image_previews(self):
        for i in reversed(range(self.image_preview_layout.count())): 
            widget = self.image_preview_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        thumbnail_size = 100
        for i, path in enumerate(self.selected_image_paths):
            logging.debug(f"Tentando carregar miniatura para preview: {path}")
            if os.path.exists(path):
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    thumbnail = pixmap.scaled(thumbnail_size, thumbnail_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    label = QLabel()
                    label.setPixmap(thumbnail)
                    label.setFixedSize(thumbnail_size, thumbnail_size)
                    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.image_preview_layout.addWidget(label, i // 4, i % 4)
                    logging.debug(f"Miniatura carregada com sucesso: {path}")
                else:
                    logging.error(f"Erro ao carregar miniatura (QPixmap is null): {path}")
            else:
                logging.error(f"Arquivo de imagem para miniatura não encontrado: {path}")

    def _save_product(self):
        nome_produto = self.name_input.text().strip()
        codigo_produto = self.code_input.text().strip()
        descricao = self.desc_input.text().strip()
        marca_id = self.brand_combobox.currentData()
        quantidade_inicial = self.qty_spinbox.value()

        if not nome_produto:
            QMessageBox.warning(self, "Erro de Validação", "O nome do produto é obrigatório.")
            logging.warning("Tentativa de salvar produto sem nome.")
            return
        
        if marca_id == -1:
            QMessageBox.warning(self, "Erro de Validação", "Por favor, selecione uma marca válida.")
            logging.warning("Tentativa de salvar produto sem marca válida.")
            return
        
        localizacao = self.location_input.text().strip()

        if self.db.add_produto(nome_produto, codigo_produto if codigo_produto else None, descricao, marca_id, quantidade_inicial, localizacao if localizacao else None):
            product_id = self.db.cursor.lastrowid
            logging.debug(f"Produto salvo com ID: {product_id}")
            
            if product_id and self.selected_image_paths:
                app_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.abspath(os.path.join(app_dir, '..'))
                images_base_dir = os.path.join(project_root, "product_images")
                
                os.makedirs(images_base_dir, exist_ok=True)
                logging.debug(f"Diretório base de imagens garantido: {images_base_dir}")

                product_images_dir = os.path.join(images_base_dir, str(product_id))
                os.makedirs(product_images_dir, exist_ok=True)
                logging.debug(f"Diretório de imagens do produto garantido: {product_images_dir}")

                for original_path in self.selected_image_paths:
                    if os.path.exists(original_path):
                        file_name = os.path.basename(original_path)
                        destination_path = os.path.join(product_images_dir, file_name)
                        shutil.copy(original_path, destination_path)
                        
                        absolute_destination_path = os.path.abspath(destination_path)
                        self.db.add_product_image(product_id, absolute_destination_path)
                        logging.debug(f"Imagem copiada e caminho salvo no DB: {absolute_destination_path}")
                    else:
                        logging.error(f"Erro: Arquivo de imagem original não encontrado: {original_path}")
            
            QMessageBox.information(self, "Sucesso", "Produto salvo com sucesso!")
            self.product_added.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível salvar o produto. Verifique se o código do produto já existe.")
            logging.error("Erro ao salvar produto no DB.")
