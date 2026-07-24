import sys
import os

# Suppress annoying GTK/ALSA/Qt platform plugin warnings during import and initialization
saved_stderr_fd = None
if sys.platform.startswith('linux'):
    try:
        stderr_fd = sys.stderr.fileno()
        saved_stderr_fd = os.dup(stderr_fd)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, stderr_fd)
        os.close(devnull)
    except OSError:
        pass

import uuid
import zipfile
import shutil
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import gc

import core

# --- Security Helpers ---
MAX_VAULT_FILE_SIZE_MB = 100  # Default max file size for vault (MB)

def validate_file_path(path):
    return core.validate_file_path(path)

from PySide6.QtCore import Qt, QSize, QCoreApplication, QTimer, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QCheckBox,
    QTextEdit, QFileDialog, QFrame, QStackedWidget, QGridLayout,
    QGraphicsDropShadowEffect, QComboBox, QProgressBar, QTabWidget,
    QDialog
)
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPainterPath, QLinearGradient

# --- Worker Threads ---
class CleanerWorker(QThread):
    file_started = Signal(int, str)
    file_finished = Signal(int, bool, str, str)
    all_finished = Signal()

    def __init__(self, files, overwrite, randomize, parent=None):
        super().__init__(parent)
        self.files = files
        self.overwrite = overwrite
        self.randomize = randomize

    def run(self):
        for i, file_info in enumerate(self.files):
            if file_info["status"] == "Başarılı":
                continue
            self.file_started.emit(i, file_info["name"])
            success, saved_path, err_msg = core.clean_file(
                file_info["path"], self.overwrite, self.randomize
            )
            self.file_finished.emit(i, success, saved_path, err_msg)
        self.all_finished.emit()


class ShredderWorker(QThread):
    file_started = Signal(int, str)
    pass_progress = Signal(str, int, int)
    file_finished = Signal(int, bool, str)
    all_finished = Signal()

    def __init__(self, files, method_index, parent=None):
        super().__init__(parent)
        self.files = files
        self.method_index = method_index

    def run(self):
        for i, file_info in enumerate(self.files):
            if file_info["status"] == "Silindi":
                continue
            filename = file_info["name"]
            self.file_started.emit(i, filename)

            def progress(p, total):
                self.pass_progress.emit(filename, p, total)

            success, err_msg = core.shred_file(file_info["path"], self.method_index, progress)
            self.file_finished.emit(i, success, err_msg)
        self.all_finished.emit()


class LogoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(90, 90)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        path = QPainterPath()
        path.moveTo(w / 2, 6)
        path.lineTo(w - 12, 18)
        path.quadTo(w - 12, h - 32, w / 2, h - 8)
        path.quadTo(12, h - 32, 12, 18)
        path.closeSubpath()
        
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QColor("#3584e4"))
        gradient.setColorAt(1, QColor("#1c51a3"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)
        
        pen = QPen(QColor("#ffffff"))
        pen.setWidth(3.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        painter.drawArc(w / 2 - 10, h / 2 - 16, 20, 18, 0, 180 * 16)
        painter.drawLine(w / 2 - 10, h / 2 - 7, w / 2 - 10, h / 2 - 1)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawRect(w / 2 - 13, h / 2 - 1, 26, 19)
        
        painter.setBrush(QBrush(QColor("#1c51a3")))
        painter.drawEllipse(w / 2 - 3, h / 2 + 4, 6, 6)
        
        pen_key = QPen(QColor("#1c51a3"))
        pen_key.setWidth(2)
        painter.setPen(pen_key)
        painter.drawLine(w / 2, h / 2 + 8, w / 2, h / 2 + 13)


class MiniLogoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 32)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        path = QPainterPath()
        path.moveTo(w / 2, 3)
        path.lineTo(w - 5, 8)
        path.quadTo(w - 5, h - 11, w / 2, h - 3)
        path.quadTo(5, h - 11, 5, 8)
        path.closeSubpath()
        
        painter.setBrush(QBrush(QColor("#3584e4")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)
        
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawRect(w / 2 - 5, h / 2 - 1, 10, 8)


class ToolCard(QFrame):
    def __init__(self, title, description, icon_char, bg_color_hex="#3584e4", is_active=True, on_click=None, parent=None):
        super().__init__(parent)
        self.is_active = is_active
        self.on_click = on_click
        self.setObjectName("ToolCard" if is_active else "ToolCardDisabled")
        self.setCursor(Qt.CursorShape.PointingHandCursor if is_active else Qt.CursorShape.ForbiddenCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        header_layout = QHBoxLayout()
        icon_lbl = QLabel(icon_char)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setFixedSize(40, 40)
        icon_lbl.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 800;
            color: #ffffff;
            background-color: {bg_color_hex if is_active else '#444444'};
            border-radius: 20px;
        """)
        header_layout.addWidget(icon_lbl)
        header_layout.addStretch()
        
        if not is_active:
            badge = QLabel("YAKINDA")
            badge.setStyleSheet("""
                font-size: 9px;
                font-weight: bold;
                background-color: rgba(255, 255, 255, 0.04);
                color: #666666;
                padding: 4px 10px;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.04);
            """)
            header_layout.addWidget(badge)
            
        layout.addLayout(header_layout)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {'#FFFFFF' if is_active else '#666666'}; background: transparent; border: none;")
        layout.addWidget(title_lbl)
        
        desc_lbl = QLabel(description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"font-size: 12px; color: {'#D3D3D3' if is_active else '#555555'}; background: transparent; border: none; line-height: 1.4;")
        layout.addWidget(desc_lbl)
        
        self.apply_style()

    def apply_style(self):
        if self.is_active:
            self.setStyleSheet("""
                #ToolCard {
                    background-color: #303030;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 16px;
                }
                #ToolCard:hover {
                    border-color: #3584e4;
                    background-color: #383838;
                }
            """)
            self.shadow = QGraphicsDropShadowEffect(self)
            self.shadow.setBlurRadius(15)
            self.shadow.setColor(QColor(0, 0, 0, 80))
            self.shadow.setOffset(0, 4)
            self.setGraphicsEffect(self.shadow)
        else:
            self.setStyleSheet("""
                #ToolCardDisabled {
                    background-color: rgba(48, 48, 48, 0.4);
                    border: 1px solid rgba(255, 255, 255, 0.02);
                    border-radius: 16px;
                }
            """)

    def mousePressEvent(self, event):
        if self.is_active and self.on_click and event.button() == Qt.MouseButton.LeftButton:
            self.on_click()


class DashboardWidget(QWidget):
    def __init__(self, on_select_cleaner, on_select_shredder, on_select_sanitizer, on_select_vault, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 48, 32, 32)
        layout.setSpacing(36)
        
        header_layout = QVBoxLayout()
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.logo = LogoWidget(self)
        header_layout.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("unutkan", self)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-family: 'Space Grotesk', 'Segoe UI', Arial, sans-serif;
            font-size: 40px;
            font-weight: 800;
            color: #ffffff;
            margin-top: 5px;
            letter-spacing: -1.5px;
        """)
        header_layout.addWidget(title)
        
        subtitle = QLabel("Kişisel veri güvenliğinizi artıran dijital hijyen araç kutusu.", self)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 13px; color: #b3b3b3; font-weight: 500;")
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
        
        grid = QGridLayout()
        grid.setSpacing(20)
        
        card_cleaner = ToolCard(
            title="Metadata Temizleyici",
            description="Dosyalarınızdaki (resim, ses, belge, PDF, ODF) EXIF, yazar, konum ve cihaz kimliği bilgilerini temizler.",
            icon_char="MT",
            bg_color_hex="#3584e4",
            is_active=True,
            on_click=on_select_cleaner,
            parent=self
        )
        grid.addWidget(card_cleaner, 0, 0)
        
        card_shredder = ToolCard(
            title="Güvenli Silici",
            description="Dosyaları diske rastgele veriler yazarak geri döndürülemeyecek şekilde kalıcı olarak siler.",
            icon_char="GS",
            bg_color_hex="#f66151",
            is_active=True,
            on_click=on_select_shredder,
            parent=self
        )
        grid.addWidget(card_shredder, 0, 1)
        
        card_sanitizer = ToolCard(
            title="Metin Arındırıcı",
            description="Paylaşacağınız metinlerdeki hassas verileri (e-posta, telefon, API anahtarı) gizler ve bağlantı takip kodlarını temizler.",
            icon_char="MA",
            bg_color_hex="#1ca8a3",
            is_active=True,
            on_click=on_select_sanitizer,
            parent=self
        )
        grid.addWidget(card_sanitizer, 1, 0)
        
        card_vault = ToolCard(
            title="Geçici Bellek Kasası",
            description="Hassas dosyalarınızı veya şifrelerinizi sadece RAM bellek üzerinde tutar, süre dolduğunda veya kapandığında tamamen imha eder.",
            icon_char="GB",
            bg_color_hex="#2ec27e",
            is_active=True,
            on_click=on_select_vault,
            parent=self
        )
        grid.addWidget(card_vault, 1, 1)
        
        layout.addLayout(grid)
        layout.addStretch()


class DropZone(QFrame):
    def __init__(self, on_files_dropped, on_clicked, help_text=None, parent=None):
        super().__init__(parent)
        self.on_files_dropped = on_files_dropped
        self.on_clicked = on_clicked
        self.setAcceptDrops(True)
        self.setObjectName("DropZone")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        
        self.icon_label = QLabel("[ + ]", self)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #3584e4; background: transparent; border: none;")
        layout.addWidget(self.icon_label)
        
        self.text_label = QLabel("Dosyaları Sürükleyin veya Seçmek İçin Tıklayın", self)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #FFFFFF; background: transparent; border: none;")
        layout.addWidget(self.text_label)
        
        sub_text = help_text or "Resim (JPG, PNG, WEBP), Belge (PDF, DOCX, ODT, ODS) ve Ses (MP3, FLAC)"
        self.subtext_label = QLabel(sub_text, self)
        self.subtext_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtext_label.setStyleSheet("font-size: 11px; color: #b3b3b3; background: transparent; border: none;")
        layout.addWidget(self.subtext_label)

        self.reset_style()

    def reset_style(self):
        self.setStyleSheet("""
            #DropZone {
                border: 2px dashed rgba(255, 255, 255, 0.15);
                border-radius: 16px;
                background-color: #303030;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                #DropZone {
                    border: 2px dashed #3584e4;
                    border-radius: 16px;
                    background-color: rgba(53, 132, 228, 0.05);
                }
            """)

    def dragLeaveEvent(self, event):
        self.reset_style()

    def dropEvent(self, event):
        self.reset_style()
        urls = event.mimeData().urls()
        file_paths = []
        for url in urls:
            file_path = url.toLocalFile()
            valid, real_path, err = validate_file_path(file_path)
            if valid:
                file_paths.append(real_path)
        
        if file_paths:
            self.on_files_dropped(file_paths)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_clicked()


class FileRowWidget(QWidget):
    def __init__(self, file_name, file_path, status, error_msg="", is_shred=False, on_inspect_clicked=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)
        
        ext = os.path.splitext(file_name)[1].upper().replace('.', '')
        self.icon_lbl = QLabel(ext if ext else "FILE")
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setFixedSize(46, 46)
        
        if is_shred:
            bg_color = "rgba(246, 97, 81, 0.08)"
            border_color = "rgba(246, 97, 81, 0.2)"
            text_color = "#f66151"
        else:
            bg_color = "rgba(53, 132, 228, 0.08)"
            border_color = "rgba(53, 132, 228, 0.2)"
            text_color = "#3584e4"
        
        self.icon_lbl.setStyleSheet(f"""
            font-size: 10px;
            font-weight: 800;
            color: {text_color};
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 10px;
        """)
        layout.addWidget(self.icon_lbl)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        
        self.name_lbl = QLabel(file_name)
        self.name_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #FFFFFF;")
        text_layout.addWidget(self.name_lbl)
        
        self.path_lbl = QLabel(file_path)
        self.path_lbl.setStyleSheet("font-size: 11px; color: #b3b3b3;")
        self.path_lbl.setWordWrap(False)
        text_layout.addWidget(self.path_lbl)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # Detaylı metadata inceleme butonu (Sadece temizleyicide ve dosya henüz işlenmediyse)
        if not is_shred and on_inspect_clicked and status == "Hazır":
            self.btn_inspect = QPushButton("Detay", self)
            self.btn_inspect.setObjectName("BtnInspect")
            self.btn_inspect.setFixedSize(65, 26)
            self.btn_inspect.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_inspect.setStyleSheet("""
                QPushButton {
                    font-size: 10px;
                    font-weight: bold;
                    background-color: transparent;
                    color: #b3b3b3;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 6px;
                    padding: 3px 6px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.05);
                    color: #ffffff;
                    border-color: #3584e4;
                }
            """)
            self.btn_inspect.clicked.connect(on_inspect_clicked)
            layout.addWidget(self.btn_inspect)
            
        self.status_lbl = QLabel(status)
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setFixedWidth(90)
        self.status_lbl.setStyleSheet(self.get_status_style(status, is_shred))
        if error_msg:
            self.status_lbl.setToolTip(error_msg)
        layout.addWidget(self.status_lbl)

    def get_status_style(self, status, is_shred):
        if status == "Hazır":
            return """
                font-size: 10px;
                font-weight: bold;
                color: #b3b3b3;
                background-color: rgba(255, 255, 255, 0.05);
                padding: 6px 12px;
                border-radius: 12px;
            """
        elif status == "Siliniyor..." or status == "Temizleniyor...":
            color = "#f66151" if is_shred else "#3584e4"
            bg = "rgba(246, 97, 81, 0.1)" if is_shred else "rgba(53, 132, 228, 0.1)"
            return f"""
                font-size: 10px;
                font-weight: bold;
                color: {color};
                background-color: {bg};
                padding: 6px 12px;
                border-radius: 12px;
            """
        elif status == "Silindi" or status == "Başarılı" or status == "Bellekte":
            return """
                font-size: 10px;
                font-weight: bold;
                color: #2ec27e;
                background-color: rgba(46, 194, 126, 0.1);
                padding: 6px 12px;
                border-radius: 12px;
            """
        else: # Hata
            return """
                font-size: 10px;
                font-weight: bold;
                color: #f66151;
                background-color: rgba(246, 97, 81, 0.1);
                padding: 6px 12px;
                border-radius: 12px;
            """


class MetadataDialog(QDialog):
    def __init__(self, filename, metadata, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Metadata Analizi - {filename}")
        self.setMinimumSize(480, 360)
        self.resize(500, 400)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title_lbl = QLabel(f"Dosya: {filename}")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_lbl)
        
        info_lbl = QLabel("Tespit edilen ve temizleme sırasında silinecek olan metadatalar:")
        info_lbl.setStyleSheet("font-size: 11px; color: #b3b3b3;")
        layout.addWidget(info_lbl)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #242424;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 6px;
                font-family: monospace;
                font-size: 12px;
            }
            QListWidget::item {
                background-color: #303030;
                border-radius: 6px;
                padding: 8px;
                margin-bottom: 4px;
            }
        """)
        
        if not metadata:
            item = QListWidgetItem("Temizlenecek herhangi bir hassas metadata bulunamadı.")
            item.setForeground(QColor("#2ec27e")) # Green color
            self.list_widget.addItem(item)
        else:
            for k, v in metadata.items():
                item_text = f"{k}: {v}"
                if len(item_text) > 85:
                    item_text = item_text[:82] + "..."
                item = QListWidgetItem(item_text)
                item.setForeground(QColor("#f66151")) # Red color
                self.list_widget.addItem(item)
                
        layout.addWidget(self.list_widget)
        
        btn_close = QPushButton("Kapat")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #3584e4;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #4b92e7;
            }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        
        self.setLayout(layout)
        self.setStyleSheet("QDialog { background-color: #303030; }")


class CleanerWidget(QWidget):
    def __init__(self, on_back_clicked, parent=None):
        super().__init__(parent)
        self.on_back_clicked = on_back_clicked
        self.selected_files = []
        
        self.supported_exts = [
            '.png', '.jpg', '.jpeg', '.webp',           # Images
            '.pdf',                                     # PDFs
            '.docx', '.xlsx', '.pptx',                  # MS Office
            '.odt', '.ods', '.odp',                     # OpenDocument
            '.mp3', '.flac', '.ogg', '.m4a'             # Audio
        ]

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # 1. Navigation & Header Bar
        header_bar = QHBoxLayout()
        header_bar.setContentsMargins(0, 0, 0, 8)
        
        self.btn_back = QPushButton("← Geri Dön", self)
        self.btn_back.setObjectName("BtnBack")
        self.btn_back.clicked.connect(self.on_back_clicked)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        header_bar.addWidget(self.btn_back)
        
        header_bar.addStretch()
        
        self.mini_logo = MiniLogoWidget(self)
        header_bar.addWidget(self.mini_logo)
        
        self.title_lbl = QLabel("Metadata Temizleyici", self)
        self.title_lbl.setObjectName("HeaderTitleSmall")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_bar.addWidget(self.title_lbl)
        
        header_bar.addStretch()
        
        spacer = QWidget()
        spacer.setFixedWidth(85)
        header_bar.addWidget(spacer)
        
        layout.addLayout(header_bar)

        # 2. DropZone Widget
        self.drop_zone = DropZone(
            on_files_dropped=self.handle_files_dropped,
            on_clicked=self.open_file_dialog,
            parent=self
        )
        self.drop_zone.setFixedHeight(150)
        layout.addWidget(self.drop_zone)

        # 3. Options Panel
        options_panel = QFrame()
        options_panel.setObjectName("OptionsPanel")
        options_layout = QHBoxLayout(options_panel)
        options_layout.setContentsMargins(16, 12, 16, 12)
        options_layout.setSpacing(20)
        
        self.chk_overwrite = QCheckBox("Orijinal Dosyanın Üzerine Yaz")
        self.chk_overwrite.setChecked(True)
        options_layout.addWidget(self.chk_overwrite)
        
        self.chk_randomize = QCheckBox("Dosya Adını Rastgeleleştir")
        self.chk_randomize.setChecked(False)
        options_layout.addWidget(self.chk_randomize)
        
        layout.addWidget(options_panel)

        # 4. Files List
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("FilesList")
        self.list_widget.itemDoubleClicked.connect(self.open_file_in_default_app)
        layout.addWidget(self.list_widget)

        # 5. Action Bar
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(12)
        
        self.btn_clear = QPushButton("Listeyi Temizle")
        self.btn_clear.setObjectName("BtnClear")
        self.btn_clear.clicked.connect(self.clear_list)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        action_layout.addWidget(self.btn_clear)
        
        action_layout.addStretch()
        
        self.btn_process = QPushButton("Metadata Temizle")
        self.btn_process.setObjectName("BtnProcess")
        self.btn_process.clicked.connect(self.process_files)
        self.btn_process.setCursor(Qt.CursorShape.PointingHandCursor)
        action_layout.addWidget(self.btn_process)
        
        layout.addLayout(action_layout)

        # 6. Log Console
        self.log_console = QTextEdit()
        self.log_console.setObjectName("LogConsole")
        self.log_console.setReadOnly(True)
        self.log_console.setFixedHeight(110)
        layout.addWidget(self.log_console)

        # Apply specific widget styling
        self.setStyleSheet("""
            #BtnBack {
                background-color: transparent;
                color: #b3b3b3;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
            }
            #BtnBack:hover {
                background-color: rgba(255, 255, 255, 0.03);
                color: #FFFFFF;
                border-color: #b3b3b3;
            }
            #HeaderTitleSmall {
                font-family: 'Space Grotesk', 'Segoe UI', Arial, sans-serif;
                font-size: 19px;
                font-weight: 800;
                color: #ffffff;
                letter-spacing: -0.5px;
            }
            QListWidget {
                background-color: #303030;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                padding: 8px;
            }
            QListWidget::item {
                background-color: #383838;
                border: 1px solid rgba(255, 255, 255, 0.02);
                border-radius: 10px;
                margin-bottom: 8px;
            }
            QListWidget::item:hover {
                background-color: #404040;
                border-color: rgba(53, 132, 228, 0.2);
            }
        """)

    def log(self, message, is_error=False):
        color = "#f66151" if is_error else "#2ec27e"
        self.log_console.append(f"<span style='color:{color};'>&gt; {message}</span>")
        self.log_console.ensureCursorVisible()

    def safely_clear_list(self, list_widget):
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item:
                list_widget.removeItemWidget(item)
        list_widget.clear()

    def open_file_in_default_app(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and os.path.exists(file_path):
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            self.log(f"Dosya sistem varsayılan uygulamasıyla açıldı: {os.path.basename(file_path)}")
        else:
            self.log("Açılacak dosya diskte bulunamadı veya silinmiş.", is_error=True)

    def inspect_file_metadata(self, file_path):
        try:
            if not os.path.exists(file_path):
                self.log("İncelenecek dosya diskte bulunamadı.", is_error=True)
                return
                
            self.log(f"Metadata inceleniyor: {os.path.basename(file_path)}")
            metadata = core.extract_file_metadata(file_path)
            
            top_window = self.window()
            dialog = MetadataDialog(os.path.basename(file_path), metadata, top_window)
            dialog.exec()
        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Hata", f"Detay penceresi açılırken bir hata oluştu:\n{err_msg}")

    def extract_file_metadata(self, file_path):
        return core.extract_file_metadata(file_path)

    def process_files(self):
        if not self.selected_files:
            self.log("Listede temizlenecek dosya yok.", is_error=True)
            return

        self.set_ui_enabled(False)
        self.log("Temizleme işlemi başlatılıyor...")
        
        overwrite = self.chk_overwrite.isChecked()
        randomize = self.chk_randomize.isChecked()
        
        self.worker = CleanerWorker(self.selected_files, overwrite, randomize)
        self.worker.file_started.connect(self._on_clean_started)
        self.worker.file_finished.connect(self._on_clean_finished)
        self.worker.all_finished.connect(self._on_clean_all_finished)
        self.worker.start()

    def _on_clean_started(self, index, filename):
        self.selected_files[index]["status"] = "Temizleniyor..."
        self.refresh_list()
        self.log(f"İşleniyor: {filename}")

    def _on_clean_finished(self, index, success, saved_path, err_msg):
        file_info = self.selected_files[index]
        if success:
            file_info["status"] = "Başarılı"
            file_info["name"] = os.path.basename(saved_path)
            file_info["path"] = saved_path
            self.log(f"Başarılı: {os.path.basename(saved_path)}")
        else:
            file_info["status"] = "Hata"
            file_info["error"] = err_msg
            self.log(f"Hata: {file_info['name']} ({err_msg})", is_error=True)
        self.refresh_list()

    def _on_clean_all_finished(self):
        self.log("İşlem tamamlandı.")
        self.set_ui_enabled(True)


class ShredderWidget(QWidget):
    def __init__(self, on_back_clicked, parent=None):
        super().__init__(parent)
        self.on_back_clicked = on_back_clicked
        self.selected_files = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        header_bar = QHBoxLayout()
        header_bar.setContentsMargins(0, 0, 0, 8)
        
        self.btn_back = QPushButton("← Geri Dön", self)
        self.btn_back.setObjectName("BtnBack")
        self.btn_back.clicked.connect(self.on_back_clicked)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        header_bar.addWidget(self.btn_back)
        
        header_bar.addStretch()
        
        self.mini_logo = MiniLogoWidget(self)
        header_bar.addWidget(self.mini_logo)
        
        self.title_lbl = QLabel("Güvenli Dosya Silici", self)
        self.title_lbl.setObjectName("HeaderTitleSmall")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_bar.addWidget(self.title_lbl)
        
        header_bar.addStretch()
        
        spacer = QWidget()
        spacer.setFixedWidth(85)
        header_bar.addWidget(spacer)
        
        layout.addLayout(header_bar)

        self.drop_zone = DropZone(
            on_files_dropped=self.handle_files_dropped,
            on_clicked=self.open_file_dialog,
            help_text="Silmek istediğiniz her türlü dosyayı buraya bırakabilirsiniz.",
            parent=self
        )
        self.drop_zone.setFixedHeight(140)
        layout.addWidget(self.drop_zone)

        options_panel = QFrame()
        options_panel.setObjectName("OptionsPanel")
        options_layout = QHBoxLayout(options_panel)
        options_layout.setContentsMargins(16, 12, 16, 12)
        options_layout.setSpacing(14)
        
        label_method = QLabel("Silme Yöntemi:")
        label_method.setStyleSheet("font-size: 13px; font-weight: bold;")
        options_layout.addWidget(label_method)
        
        self.combo_method = QComboBox()
        self.combo_method.addItems([
            "Hızlı Sıfırla (1 Geçiş - Sıfır Yazma)",
            "Güvenli (3 Geçiş - Rastgele + Sıfır)",
            "Maksimum Güvenlik (7 Geçiş - Çoklu Desen)"
        ])
        self.combo_method.setCurrentIndex(1)
        options_layout.addWidget(self.combo_method)
        options_layout.addStretch()
        
        layout.addWidget(options_panel)

        self.warning_lbl = QLabel("UYARI: Güvenli silinen dosyalar kurtarılamaz ve diskten kalıcı olarak imha edilir.", self)
        self.warning_lbl.setWordWrap(True)
        self.warning_lbl.setStyleSheet("""
            font-size: 11px;
            font-weight: bold;
            color: #f66151;
            background-color: rgba(246, 97, 81, 0.08);
            border: 1px solid rgba(246, 97, 81, 0.15);
            border-radius: 8px;
            padding: 8px 12px;
        """)
        layout.addWidget(self.warning_lbl)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("FilesList")
        self.list_widget.itemDoubleClicked.connect(self.open_file_in_default_app)
        layout.addWidget(self.list_widget)

        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(12)
        
        self.btn_clear = QPushButton("Listeyi Temizle")
        self.btn_clear.setObjectName("BtnClear")
        self.btn_clear.clicked.connect(self.clear_list)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        action_layout.addWidget(self.btn_clear)
        
        action_layout.addStretch()
        
        self.btn_shred = QPushButton("Güvenli Sil (İmha Et)")
        self.btn_shred.setObjectName("BtnShred")
        self.btn_shred.clicked.connect(self.process_shredding)
        self.btn_shred.setCursor(Qt.CursorShape.PointingHandCursor)
        action_layout.addWidget(self.btn_shred)
        
        layout.addLayout(action_layout)

        self.log_console = QTextEdit()
        self.log_console.setObjectName("LogConsole")
        self.log_console.setReadOnly(True)
        self.log_console.setFixedHeight(110)
        layout.addWidget(self.log_console)

        self.setStyleSheet("""
            #BtnBack {
                background-color: transparent;
                color: #b3b3b3;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
            }
            #BtnBack:hover {
                background-color: rgba(255, 255, 255, 0.03);
                color: #FFFFFF;
                border-color: #b3b3b3;
            }
            #HeaderTitleSmall {
                font-family: 'Space Grotesk', 'Segoe UI', Arial, sans-serif;
                font-size: 19px;
                font-weight: 800;
                color: #ffffff;
                letter-spacing: -0.5px;
            }
            QListWidget {
                background-color: #303030;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                padding: 8px;
            }
            QListWidget::item {
                background-color: #383838;
                border: 1px solid rgba(255, 255, 255, 0.02);
                border-radius: 10px;
                margin-bottom: 8px;
            }
            QListWidget::item:hover {
                background-color: #404040;
                border-color: rgba(246, 97, 81, 0.2);
            }
            #BtnShred {
                background-color: #f66151;
                color: #ffffff;
                border: none;
            }
            #BtnShred:hover {
                background-color: #f88172;
            }
            #BtnShred:pressed {
                background-color: #c0483c;
            }
        """)

    def log(self, message, is_error=False):
        color = "#f66151" if is_error else "#2ec27e"
        self.log_console.append(f"<span style='color:{color};'>&gt; {message}</span>")
        self.log_console.ensureCursorVisible()

    def safely_clear_list(self, list_widget):
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item:
                list_widget.removeItemWidget(item)
        list_widget.clear()

    def open_file_in_default_app(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and os.path.exists(file_path):
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            self.log(f"Dosya açıldı: {os.path.basename(file_path)}")
        else:
            self.log("Dosya açılamadı (silinmiş veya bulunamadı).", is_error=True)

    def open_file_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Güvenli Silinecek Dosyaları Seçin",
            "",
            "Tüm Dosyalar (*.*)"
        )
        if paths:
            self.handle_files_dropped(paths)

    def handle_files_dropped(self, paths):
        added_count = 0
        for path in paths:
            valid, real_path, err = validate_file_path(path)
            if not valid:
                self.log(f"Reddedildi ({os.path.basename(path)}): {err}", is_error=True)
                continue

            if any(f["path"] == real_path for f in self.selected_files):
                continue
            
            file_info = {
                "path": real_path,
                "name": os.path.basename(real_path),
                "status": "Hazır",
                "error": ""
            }
            self.selected_files.append(file_info)
            added_count += 1
        
        if added_count > 0:
            self.log(f"{added_count} adet dosya silme sırasına eklendi.")
            self.refresh_list()

    def refresh_list(self):
        self.safely_clear_list(self.list_widget)
        for file_info in self.selected_files:
            item = QListWidgetItem(self.list_widget)
            item.setData(Qt.ItemDataRole.UserRole, file_info["path"])
            row_widget = FileRowWidget(
                file_info["name"],
                file_info["path"],
                file_info["status"],
                file_info["error"],
                is_shred=True
            )
            item.setSizeHint(row_widget.sizeHint())
            self.list_widget.setItemWidget(item, row_widget)

    def clear_list(self):
        self.selected_files = []
        self.safely_clear_list(self.list_widget)
        self.log_console.clear()
        self.log("Silme sırası temizlendi.")

    def set_ui_enabled(self, enabled):
        self.btn_shred.setEnabled(enabled)
        self.btn_clear.setEnabled(enabled)
        self.combo_method.setEnabled(enabled)
        self.drop_zone.setAcceptDrops(enabled)
        self.btn_back.setEnabled(enabled)
        if not enabled:
            self.btn_shred.setText("Siliniyor...")
        else:
            self.btn_shred.setText("Güvenli Sil (İmha Et)")

    def process_shredding(self):
        if not self.selected_files:
            self.log("Silinecek dosya seçilmedi.", is_error=True)
            return

        self.set_ui_enabled(False)
        self.log("Güvenli imha işlemi başlatılıyor...")
        
        method_index = self.combo_method.currentIndex()
        
        self.worker = ShredderWorker(self.selected_files, method_index)
        self.worker.file_started.connect(self._on_shred_started)
        self.worker.pass_progress.connect(self._on_shred_pass_progress)
        self.worker.file_finished.connect(self._on_shred_finished)
        self.worker.all_finished.connect(self._on_shred_all_finished)
        self.worker.start()

    def _on_shred_started(self, index, filename):
        self.selected_files[index]["status"] = "Siliniyor..."
        self.refresh_list()
        self.log(f"İmha ediliyor: {filename}")

    def _on_shred_pass_progress(self, filename, pass_num, total_passes):
        self.log(f"  [{filename}] Geçiş {pass_num}/{total_passes} yazılıyor...")

    def _on_shred_finished(self, index, success, err_msg):
        file_info = self.selected_files[index]
        if success:
            file_info["status"] = "Silindi"
            self.log(f"İmha Edildi (Geri döndürülemez): {file_info['name']}")
        else:
            file_info["status"] = "Hata"
            file_info["error"] = err_msg
            self.log(f"Hata: {file_info['name']} ({err_msg})", is_error=True)
        self.refresh_list()

    def _on_shred_all_finished(self):
        self.log("Tüm imha işlemleri tamamlandı.")
        self.set_ui_enabled(True)


class SanitizerWidget(QWidget):
    def __init__(self, on_back_clicked, parent=None):
        super().__init__(parent)
        self.on_back_clicked = on_back_clicked
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        header_bar = QHBoxLayout()
        header_bar.setContentsMargins(0, 0, 0, 8)
        
        self.btn_back = QPushButton("← Geri Dön", self)
        self.btn_back.setObjectName("BtnBack")
        self.btn_back.clicked.connect(self.on_back_clicked)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        header_bar.addWidget(self.btn_back)
        
        header_bar.addStretch()
        
        self.mini_logo = MiniLogoWidget(self)
        header_bar.addWidget(self.mini_logo)
        
        self.title_lbl = QLabel("Metin Arındırıcı", self)
        self.title_lbl.setObjectName("HeaderTitleSmall")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_bar.addWidget(self.title_lbl)
        
        header_bar.addStretch()
        
        spacer = QWidget()
        spacer.setFixedWidth(85)
        header_bar.addWidget(spacer)
        
        layout.addLayout(header_bar)

        label_input = QLabel("Arındırılacak Ham Metin:")
        label_input.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(label_input)

        self.txt_input = QTextEdit()
        self.txt_input.setPlaceholderText("Arındırılacak metni, linkleri veya log kayıtlarını buraya yapıştırın...")
        layout.addWidget(self.txt_input)

        options_panel = QFrame()
        options_panel.setObjectName("OptionsPanel")
        options_layout = QGridLayout(options_panel)
        options_layout.setContentsMargins(16, 14, 16, 14)
        options_layout.setSpacing(14)
        
        self.chk_links = QCheckBox("Bağlantı Takip Parametrelerini Temizle (utm_*, fbclid vb.)")
        self.chk_links.setChecked(True)
        options_layout.addWidget(self.chk_links, 0, 0)
        
        self.chk_emails = QCheckBox("E-posta Adreslerini Maskele")
        self.chk_emails.setChecked(True)
        options_layout.addWidget(self.chk_emails, 0, 1)
        
        self.chk_phones = QCheckBox("Telefon Numaralarını Maskele")
        self.chk_phones.setChecked(True)
        options_layout.addWidget(self.chk_phones, 1, 0)
        
        self.chk_secrets = QCheckBox("API Anahtarları ve Parolaları Maskele")
        self.chk_secrets.setChecked(True)
        options_layout.addWidget(self.chk_secrets, 1, 1)
        
        layout.addWidget(options_panel)

        label_output = QLabel("Arındırılmış Sonuç:")
        label_output.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(label_output)

        self.txt_output = QTextEdit()
        self.txt_output.setReadOnly(True)
        self.txt_output.setPlaceholderText("Arındırılan metin burada görüntülenecektir...")
        layout.addWidget(self.txt_output)

        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(12)
        
        self.btn_clear = QPushButton("Metni Temizle")
        self.btn_clear.setObjectName("BtnClear")
        self.btn_clear.clicked.connect(self.clear_text)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        action_layout.addWidget(self.btn_clear)
        
        action_layout.addStretch()
        
        self.btn_copy = QPushButton("Panoya Kopyala")
        self.btn_copy.setObjectName("BtnClear")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        action_layout.addWidget(self.btn_copy)
        
        self.btn_sanitize = QPushButton("Metni Arındır")
        self.btn_sanitize.setObjectName("BtnProcess")
        self.btn_sanitize.clicked.connect(self.process_sanitization)
        self.btn_sanitize.setCursor(Qt.CursorShape.PointingHandCursor)
        action_layout.addWidget(self.btn_sanitize)
        
        layout.addLayout(action_layout)

        self.setStyleSheet("""
            #BtnBack {
                background-color: transparent;
                color: #b3b3b3;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
            }
            #BtnBack:hover {
                background-color: rgba(255, 255, 255, 0.03);
                color: #FFFFFF;
                border-color: #b3b3b3;
            }
            #HeaderTitleSmall {
                font-family: 'Space Grotesk', 'Segoe UI', Arial, sans-serif;
                font-size: 19px;
                font-weight: 800;
                color: #ffffff;
                letter-spacing: -0.5px;
            }
            QTextEdit {
                background-color: #303030;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                padding: 10px;
                font-size: 13px;
            }
        """)

    def clear_text(self):
        self.txt_input.clear()
        self.txt_output.clear()

    def copy_to_clipboard(self):
        text = self.txt_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.btn_copy.setText("✓ Kopyalandı!")
            QTimer.singleShot(2000, lambda: self.btn_copy.setText("Panoya Kopyala"))

    def process_sanitization(self):
        text = self.txt_input.toPlainText()
        if not text:
            return
            
        clean_links = self.chk_links.isChecked()
        mask_emails = self.chk_emails.isChecked()
        mask_phones = self.chk_phones.isChecked()
        mask_secrets = self.chk_secrets.isChecked()
        
        sanitized = self.sanitize_text(text, clean_links, mask_emails, mask_phones, mask_secrets)
        self.txt_output.setPlainText(sanitized)

    def sanitize_text(self, text, clean_links, mask_emails, mask_phones, mask_secrets):
        settings = {
            'urls': clean_links,
            'emails': mask_emails,
            'phones': mask_phones,
            'secrets': mask_secrets
        }
        return core.sanitize_text(text, settings)


class VaultWidget(QWidget):
    def __init__(self, on_back_clicked, parent=None):
        super().__init__(parent)
        self.on_back_clicked = on_back_clicked
        self.vault = core.RamVault()
        self.time_left = 0
        self.total_time = 120
        self.max_file_size_mb = MAX_VAULT_FILE_SIZE_MB
        
        # QTimer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer_tick)
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # 1. Navigation & Header Bar
        header_bar = QHBoxLayout()
        header_bar.setContentsMargins(0, 0, 0, 8)
        
        self.btn_back = QPushButton("← Geri Dön", self)
        self.btn_back.setObjectName("BtnBack")
        self.btn_back.clicked.connect(self.on_back_clicked)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        header_bar.addWidget(self.btn_back)
        
        header_bar.addStretch()
        
        self.mini_logo = MiniLogoWidget(self)
        header_bar.addWidget(self.mini_logo)
        
        self.title_lbl = QLabel("Geçici Bellek Kasası", self)
        self.title_lbl.setObjectName("HeaderTitleSmall")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_bar.addWidget(self.title_lbl)
        
        header_bar.addStretch()
        
        spacer = QWidget()
        spacer.setFixedWidth(85)
        header_bar.addWidget(spacer)
        
        layout.addLayout(header_bar)

        # 2. Main Horizontal Body (Split into Left Controls and Right Tabs)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(20)

        # Left Panel (Timer, Vault Status, Wipe button)
        left_panel = QFrame()
        left_panel.setObjectName("OptionsPanel")
        left_panel.setFixedWidth(240)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(14)

        status_lbl = QLabel("KASA DURUMU:")
        status_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #b3b3b3;")
        left_layout.addWidget(status_lbl)

        self.lbl_status_val = QLabel("KİLİTLİ / BOŞ")
        self.lbl_status_val.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #f66151;
            background-color: rgba(246, 97, 81, 0.08);
            border: 1px solid rgba(246, 97, 81, 0.15);
            border-radius: 8px;
            padding: 8px;
            alignment: center;
        """)
        self.lbl_status_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.lbl_status_val)

        left_layout.addWidget(QLabel("Kapanma Süresi:"))
        self.combo_duration = QComboBox()
        self.combo_duration.addItems([
            "30 Saniye",
            "2 Dakika",
            "5 Dakika",
            "10 Dakika"
        ])
        self.combo_duration.setCurrentIndex(1) # Default 2 minutes
        self.combo_duration.currentIndexChanged.connect(self.on_duration_changed)
        left_layout.addWidget(self.combo_duration)

        self.lbl_timer = QLabel("Kalan Süre: -- sn")
        self.lbl_timer.setStyleSheet("font-size: 12px; font-weight: bold; color: #ffffff;")
        left_layout.addWidget(self.lbl_timer)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #242424;
                border-radius: 4px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #2ec27e;
                border-radius: 4px;
            }
        """)
        left_layout.addWidget(self.progress_bar)
        
        left_layout.addWidget(QLabel("Maks. Dosya Boyutu:"))
        self.combo_max_size = QComboBox()
        self.combo_max_size.addItems([
            "50 MB",
            "100 MB",
            "250 MB",
            "500 MB",
            "1 GB",
            "Limitsiz"
        ])
        self.combo_max_size.setCurrentIndex(1)  # Default 100 MB
        self.combo_max_size.currentIndexChanged.connect(self.on_max_size_changed)
        left_layout.addWidget(self.combo_max_size)

        left_layout.addStretch()

        self.btn_wipe = QPushButton("Belleği Şimdi Kazı (Wipe)")
        self.btn_wipe.setObjectName("BtnWipe")
        self.btn_wipe.clicked.connect(self.wipe_vault)
        self.btn_wipe.setCursor(Qt.CursorShape.PointingHandCursor)
        left_layout.addWidget(self.btn_wipe)

        body_layout.addWidget(left_panel)

        # Right Panel (Tabbed Data View)
        self.tab_widget = QTabWidget()
        
        # Tab 1: Metin Kasası
        tab_text = QWidget()
        tab_text_layout = QVBoxLayout(tab_text)
        tab_text_layout.setContentsMargins(12, 12, 12, 12)
        tab_text_layout.setSpacing(12)
        
        self.txt_vault_input = QTextEdit()
        self.txt_vault_input.setPlaceholderText("Bellekte geçici olarak tutulacak şifre, not veya hassas metinleri girin...")
        tab_text_layout.addWidget(self.txt_vault_input)
        
        btn_text_layout = QHBoxLayout()
        btn_text_layout.setSpacing(12)
        
        self.btn_lock_text = QPushButton("Kilitle & Gizle")
        self.btn_lock_text.setObjectName("BtnProcess") # Blue action style
        self.btn_lock_text.clicked.connect(self.lock_text_to_ram)
        self.btn_lock_text.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_text_layout.addWidget(self.btn_lock_text)
        
        self.btn_unlock_text = QPushButton("Belleği Çöz / Göster")
        self.btn_unlock_text.setObjectName("BtnClear") # Clear border style
        self.btn_unlock_text.clicked.connect(self.unlock_text_from_ram)
        self.btn_unlock_text.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_text_layout.addWidget(self.btn_unlock_text)
        
        tab_text_layout.addLayout(btn_text_layout)
        
        self.tab_widget.addTab(tab_text, "Metin Kasası")

        # Tab 2: Dosya Kasası
        tab_files = QWidget()
        tab_files_layout = QVBoxLayout(tab_files)
        tab_files_layout.setContentsMargins(12, 12, 12, 12)
        tab_files_layout.setSpacing(12)
        
        self.vault_drop_zone = DropZone(
            on_files_dropped=self.handle_files_dropped,
            on_clicked=self.open_file_dialog,
            help_text="RAM'e yüklemek istediğiniz dosyaları sürükleyin.",
            parent=self
        )
        self.vault_drop_zone.setFixedHeight(90)
        tab_files_layout.addWidget(self.vault_drop_zone)
        
        self.list_files = QListWidget()
        self.list_files.setObjectName("FilesList")
        tab_files_layout.addWidget(self.list_files)
        
        btn_files_layout = QHBoxLayout()
        btn_files_layout.setSpacing(12)
        
        self.btn_export = QPushButton("Dosyayı Dışarı Aktar (Diske Kaydet)")
        self.btn_export.setObjectName("BtnProcess")
        self.btn_export.clicked.connect(self.export_selected_file)
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_files_layout.addWidget(self.btn_export)
        
        tab_files_layout.addLayout(btn_files_layout)
        
        self.tab_widget.addTab(tab_files, "Dosya Kasası")

        body_layout.addWidget(self.tab_widget)
        layout.addLayout(body_layout)

        # 3. Log Console
        self.log_console = QTextEdit()
        self.log_console.setObjectName("LogConsole")
        self.log_console.setReadOnly(True)
        self.log_console.setFixedHeight(110)
        layout.addWidget(self.log_console)

        # Apply specific widget styling
        self.setStyleSheet("""
            #BtnBack {
                background-color: transparent;
                color: #b3b3b3;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
            }
            #BtnBack:hover {
                background-color: rgba(255, 255, 255, 0.03);
                color: #FFFFFF;
                border-color: #b3b3b3;
            }
            #HeaderTitleSmall {
                font-family: 'Space Grotesk', 'Segoe UI', Arial, sans-serif;
                font-size: 19px;
                font-weight: 800;
                color: #ffffff;
                letter-spacing: -0.5px;
            }
            #BtnWipe {
                background-color: #f66151;
                color: #ffffff;
                border: none;
                font-size: 12px;
            }
            #BtnWipe:hover {
                background-color: #f88172;
            }
            #BtnWipe:pressed {
                background-color: #c0483c;
            }
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 0.05);
                background-color: #303030;
                border-radius: 12px;
                padding: 4px;
            }
            QTabBar::tab {
                background: #242424;
                border: 1px solid rgba(255, 255, 255, 0.05);
                padding: 8px 16px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
                font-size: 12px;
                font-weight: bold;
                color: #b3b3b3;
            }
            QTabBar::tab:selected {
                background: #303030;
                border-bottom-color: #303030;
                color: #ffffff;
            }
            QListWidget {
                background-color: #242424;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                padding: 8px;
            }
            QListWidget::item {
                background-color: #303030;
                border: 1px solid rgba(255, 255, 255, 0.02);
                border-radius: 10px;
                margin-bottom: 8px;
            }
            QListWidget::item:hover {
                background-color: #383838;
            }
        """)

    def log(self, message, is_error=False):
        color = "#f66151" if is_error else "#2ec27e"
        self.log_console.append(f"<span style='color:{color};'>&gt; {message}</span>")
        self.log_console.ensureCursorVisible()

    def safely_clear_list(self, list_widget):
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item:
                list_widget.removeItemWidget(item)
        list_widget.clear()

    def get_selected_duration(self):
        idx = self.combo_duration.currentIndex()
        if idx == 0:
            return 30
        elif idx == 1:
            return 120
        elif idx == 2:
            return 300
        else:
            return 600

    def on_max_size_changed(self, index):
        sizes = [50, 100, 250, 500, 1024, 0]  # 0 = unlimited
        self.max_file_size_mb = sizes[index]
        if self.max_file_size_mb == 0:
            self.log("Dosya boyutu limiti kaldırıldı (Dikkat: büyük dosyalar sistemi yavaşlatabilir).")
            self.max_file_size_mb = 999999  # Effectively unlimited
        else:
            self.log(f"Maksimum dosya boyutu {self.max_file_size_mb} MB olarak ayarlandı.")

    def on_duration_changed(self):
        if self.timer.isActive():
            self.total_time = self.get_selected_duration()
            self.time_left = self.total_time
            self.log(f"Zamanlayıcı süresi güncellendi: {self.total_time} sn.")

    def start_vault_timer(self):
        self.total_time = self.get_selected_duration()
        self.time_left = self.total_time
        
        self.lbl_status_val.setText("BELLEK AKTİF")
        self.lbl_status_val.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2ec27e;
            background-color: rgba(46, 194, 126, 0.08);
            border: 1px solid rgba(46, 194, 126, 0.15);
            border-radius: 8px;
            padding: 8px;
        """)
        
        self.progress_bar.setValue(100)
        self.lbl_timer.setText(f"Kalan Süre: {self.time_left} sn")
        
        self.timer.start(1000)

    def on_timer_tick(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.lbl_timer.setText(f"Kalan Süre: {self.time_left} sn")
            percentage = int((self.time_left / self.total_time) * 100)
            self.progress_bar.setValue(percentage)
        else:
            self.timer.stop()
            self.wipe_vault()
            self.log("[!] ZAMAN AŞIMI: Bellek kilitlendi ve veriler kazındı.")

    def lock_text_to_ram(self):
        text = self.txt_vault_input.toPlainText()
        if not text:
            self.log("Belleğe yüklenecek metin girilmedi.", is_error=True)
            return
            
        self.vault.mem_text = bytearray(text, 'utf-8')
        del text  # Remove reference to immutable str copy
        gc.collect()  # Best-effort garbage collection
        self.txt_vault_input.clear()
        self.log("Metin verisi RAM belleğe yüklendi ve ekran temizlendi.")
        self.start_vault_timer()

    def unlock_text_from_ram(self):
        if self.vault.mem_text:
            try:
                decoded = self.vault.mem_text.decode('utf-8')
                self.txt_vault_input.setPlainText(decoded)
                self.log("Metin verisi bellekten okunarak ekrana getirildi.")
            except Exception as e:
                self.log(f"Metin çözme hatası: {str(e)}", is_error=True)
        else:
            self.log("Bellekte çözülecek veri bulunamadı (Kilitli veya Boş).", is_error=True)

    def open_file_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "RAM Belleğe Yüklenecek Dosyaları Seçin",
            "",
            "Tüm Dosyalar (*.*)"
        )
        if paths:
            self.handle_files_dropped(paths)

    def handle_files_dropped(self, paths):
        added = 0
        max_size = self.max_file_size_mb * 1024 * 1024
        for path in paths:
            valid, real_path, err = validate_file_path(path)
            if not valid:
                self.log(f"Reddedildi ({os.path.basename(path)}): {err}", is_error=True)
                continue
            
            file_size = os.path.getsize(real_path)
            if file_size > max_size:
                size_mb = file_size / (1024 * 1024)
                self.log(f"Reddedildi ({os.path.basename(real_path)}): Dosya boyutu ({size_mb:.1f} MB) belirlenen limiti ({self.max_file_size_mb} MB) aşıyor.", is_error=True)
                continue

            filename = os.path.basename(real_path)
            try:
                with open(real_path, 'rb') as f:
                    data = f.read()
                # Store as mutable bytearray in memory, delete immutable bytes copy
                self.vault.mem_files[filename] = bytearray(data)
                del data
                gc.collect()
                self.log(f"Dosya RAM belleğe yüklendi: {filename} ({file_size} bayt)")
                added += 1
            except Exception as e:
                self.log(f"Dosya yükleme hatası ({filename}): {str(e)}", is_error=True)
                
        if added > 0:
            self.refresh_file_list()
            self.start_vault_timer()

    def refresh_file_list(self):
        self.safely_clear_list(self.list_files)
        for filename, data in self.vault.mem_files.items():
            item = QListWidgetItem(self.list_files)
            # Store filename in user role data
            item.setData(Qt.ItemDataRole.UserRole, filename)
            row_widget = FileRowWidget(
                filename,
                f"RAM Bellek üzerinde tamponlandı ({len(data)} bayt)",
                "Bellekte",
                is_shred=False
            )
            item.setSizeHint(row_widget.sizeHint())
            self.list_files.setItemWidget(item, row_widget)

    def export_selected_file(self):
        selected_items = self.list_files.selectedItems()
        if not selected_items:
            self.log("Dışarı aktarılacak dosya seçilmedi.", is_error=True)
            return
            
        filename = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if filename in self.vault.mem_files:
            file_data = self.vault.mem_files[filename]
            save_path, _ = QFileDialog.getSaveFileName(self, "Dosyayı Dışarı Aktar", filename, "Tüm Dosyalar (*.*)")
            if save_path:
                try:
                    with open(save_path, 'wb') as f:
                        f.write(file_data)
                    self.log(f"Dosya diskte başarıyla oluşturuldu: {os.path.basename(save_path)}")
                except Exception as e:
                    self.log(f"Dosya yazılırken hata oluştu: {str(e)}", is_error=True)

    def wipe_vault(self):
        try:
            self.timer.stop()
            self.progress_bar.setValue(0)
            self.lbl_timer.setText("Kalan Süre: -- sn")
            
            self.lbl_status_val.setText("KİLİTLİ / BOŞ")
            self.lbl_status_val.setStyleSheet("""
                font-size: 14px;
                font-weight: bold;
                color: #f66151;
                background-color: rgba(246, 97, 81, 0.08);
                border: 1px solid rgba(246, 97, 81, 0.15);
                border-radius: 8px;
                padding: 8px;
            """)

            # Clear log history to avoid leaking filenames in log console
            self.log_console.clear()

            # Delegate wipe to RamVault core
            def log_callback(msg):
                self.log(msg)
            self.vault.wipe(log_callback)
                
            self.safely_clear_list(self.list_files)
            self.txt_vault_input.clear()
            gc.collect()
            self.log("Geçici bellek tamamen kazındı, kasa kilitlendi.")
        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Hata", f"Bellek temizlenirken bir hata oluştu:\n{err_msg}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Unutkan - Güvenli Dijital Hijyen Araç Kutusu")
        self.setMinimumSize(720, 820)
        self.resize(720, 820)
        
        # Stacked Widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.dashboard_widget = DashboardWidget(
            on_select_cleaner=self.show_cleaner, 
            on_select_shredder=self.show_shredder, 
            on_select_sanitizer=self.show_sanitizer,
            on_select_vault=self.show_vault,
            parent=self
        )
        self.cleaner_widget = CleanerWidget(on_back_clicked=self.show_dashboard, parent=self)
        self.shredder_widget = ShredderWidget(on_back_clicked=self.show_dashboard, parent=self)
        self.sanitizer_widget = SanitizerWidget(on_back_clicked=self.show_dashboard, parent=self)
        self.vault_widget = VaultWidget(on_back_clicked=self.show_dashboard, parent=self)
        
        self.stacked_widget.addWidget(self.dashboard_widget)
        self.stacked_widget.addWidget(self.cleaner_widget)
        self.stacked_widget.addWidget(self.shredder_widget)
        self.stacked_widget.addWidget(self.sanitizer_widget)
        self.stacked_widget.addWidget(self.vault_widget)
        
        self.apply_styles()
        self.show_dashboard()

    def show_dashboard(self):
        self.stacked_widget.setCurrentWidget(self.dashboard_widget)

    def show_cleaner(self):
        self.stacked_widget.setCurrentWidget(self.cleaner_widget)

    def show_shredder(self):
        self.stacked_widget.setCurrentWidget(self.shredder_widget)

    def show_sanitizer(self):
        self.stacked_widget.setCurrentWidget(self.sanitizer_widget)

    def show_vault(self):
        self.stacked_widget.setCurrentWidget(self.vault_widget)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #242424;
            }
            QWidget {
                color: #ffffff;
                font-family: 'Cantarell', 'Inter', 'Segoe UI', Arial, sans-serif;
            }
            #OptionsPanel {
                background-color: #303030;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
            }
            QCheckBox {
                font-size: 13px;
                font-weight: 500;
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                background-color: #242424;
            }
            QCheckBox::indicator:checked {
                background-color: #3584e4;
                border-color: #3584e4;
            }
            #LogConsole {
                background-color: #1e1e1e;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                font-family: 'Courier New', Courier, monospace;
                font-size: 12px;
                color: #78aeed;
                padding: 10px;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 5px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.08);
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(53, 132, 228, 0.4);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: transparent;
                height: 0px;
            }
            QPushButton {
                font-size: 13px;
                font-weight: 700;
                border-radius: 10px;
                padding: 10px 24px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            #BtnProcess {
                background-color: #3584e4;
                color: #ffffff;
                border: none;
            }
            #BtnProcess:hover {
                background-color: #4b92e7;
            }
            #BtnProcess:pressed {
                background-color: #276cb8;
            }
            #BtnClear {
                background-color: transparent;
                color: #b3b3b3;
            }
            #BtnClear:hover {
                background-color: rgba(255, 255, 255, 0.02);
                color: #ffffff;
                border-color: #b3b3b3;
            }
            QComboBox {
                background-color: #242424;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
                color: #ffffff;
                min-width: 160px;
            }
            QComboBox::drop-down {
                border: none;
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #303030;
                border: 1px solid rgba(255, 255, 255, 0.1);
                selection-background-color: #3584e4;
                selection-color: #ffffff;
                color: #ffffff;
                padding: 4px;
            }
        """)

def main():
    app = QApplication(sys.argv)

    # Restore stderr
    global saved_stderr_fd
    if sys.platform.startswith('linux') and saved_stderr_fd is not None:
        try:
            stderr_fd = sys.stderr.fileno()
            os.dup2(saved_stderr_fd, stderr_fd)
            os.close(saved_stderr_fd)
            saved_stderr_fd = None
        except OSError:
            pass

    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
