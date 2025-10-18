import sys
import os
from PyQt6.QtWidgets import QApplication
from MeuEstoque.ui.main_window import MainWindow
from MeuEstoque.database.database_manager import DatabaseManager

if __name__ == "__main__":
    # Garante que o diretório de imagens do produto exista
    app_dir = os.path.dirname(os.path.abspath(__file__))
    images_base_dir = os.path.join(app_dir, "product_images")
    os.makedirs(images_base_dir, exist_ok=True)
    print(f"DEBUG: Diretório base de imagens garantido: {images_base_dir}")
    sys.stdout.flush()

    # Garante que o banco de dados seja inicializado e as tabelas criadas
    # antes de iniciar a aplicação.
    db_manager = DatabaseManager()
    db_manager.close() # Fecha a conexão inicial, a MainWindow abrirá a sua própria.

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
