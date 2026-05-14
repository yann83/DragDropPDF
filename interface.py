import sys
import json
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QMenu, QFileDialog
from PySide6.QtCore import Qt, QPoint, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QPainter, QAction, QPixmap, QDragEnterEvent, QDropEvent, QPen

from core import GhostConverter
from config import ConfigJson


class ConversionThread(QThread):
    """
    Thread dedicated to PDF conversion to avoid blocking the UI
    """
    finished = Signal()
    error = Signal(str)

    def __init__(self, fichier_path: str, fichier_sortie: str, niveau: str):
        super().__init__()
        self.fichier_path = fichier_path
        self.fichier_sortie = fichier_sortie
        self.niveau = niveau

    def run(self):
        try:
            converter = GhostConverter(self.fichier_path, self.fichier_sortie, self.niveau)
            converter.launch()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class CarreRouge(QWidget):
    def __init__(self):
        super().__init__()

        config_json = ConfigJson(Path("config.json"))
        self.config_json_path = config_json.determine_config_path()

        # Loading the configuration
        self.config = self.charger_config()

        # Window configuration
        self.setWindowTitle("DropPDF")
        self.setFixedSize(100, 100)

        # Remove window borders and force foreground
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        # Allow mouse tracking for right click
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.afficher_menu)

        # Position the square in the bottom right corner of the screen
        screen_rect = QApplication.primaryScreen().geometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()

        pos_x = screen_width - self.width() - 100
        pos_y = screen_height - self.height() - 100
        self.move(pos_x, pos_y)

        # Determine current level and image from configuration
        self.niveau_actuel = next(iter(self.config["current"].keys()))
        self.image_actuelle = self.config["current"][self.niveau_actuel]

        # Build the full path of the image
        chemin_image = os.path.join("img", self.image_actuelle)
        if os.path.exists(chemin_image):
            self.pixmap = QPixmap(chemin_image)
        else:
            self.pixmap = None

        # --- Loading animation state ---
        self.is_converting = False
        self.spinner_angle = 0

        # Timer for the spinner animation (updates every 30ms ≈ 33fps)
        self.spinner_timer = QTimer(self)
        self.spinner_timer.timeout.connect(self._update_spinner)

        # Active conversion threads (kept alive until finished)
        self._conversion_threads = []

        # Enable drag and drop
        self.setAcceptDrops(True)

    def _update_spinner(self):
        """Advances the spinner angle and triggers a repaint"""
        self.spinner_angle = (self.spinner_angle + 8) % 360
        self.update()

    def _start_spinner(self):
        """Switches the widget into loading mode"""
        self.is_converting = True
        self.spinner_angle = 0
        self.spinner_timer.start(30)
        self.update()

    def _stop_spinner(self):
        """Switches the widget back to normal mode if no conversion is running"""
        # Only stop when every thread has finished
        alive = [t for t in self._conversion_threads if t.isRunning()]
        self._conversion_threads = alive
        if not alive:
            self.is_converting = False
            self.spinner_timer.stop()
            self.update()

    def charger_config(self):
        try:
            with open(self.config_json_path, "r") as fichier:
                return json.load(fichier)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "path": "",
                "pics": {"high": "pdf.jpg", "medium": "pdflow.jpg", "low": "pdfmedium.jpg"},
                "current": {"medium": "pdflow.jpg"}
            }

    def sauvegarder_config(self):
        try:
            with open(self.config_json_path, "w") as fichier:
                json.dump(self.config, fichier, indent=2)
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def changer_image(self, niveau):
        if niveau in self.config["pics"]:
            self.niveau_actuel = niveau
            image_nom = self.config["pics"][niveau]
            self.image_actuelle = image_nom
            self.config["current"] = {niveau: image_nom}
            self.sauvegarder_config()

            chemin_image = os.path.join("img", image_nom)
            if os.path.exists(chemin_image):
                self.pixmap = QPixmap(chemin_image)
            else:
                self.pixmap = None

            self.update()

    def paintEvent(self, event):
        peintre = QPainter(self)
        peintre.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.is_converting:
            self._draw_spinner(peintre)
        elif self.pixmap and not self.pixmap.isNull():
            peintre.drawPixmap(0, 0, self.width(), self.height(), self.pixmap)
        else:
            peintre.setBrush(QColor(255, 0, 0))
            peintre.drawRect(0, 0, self.width(), self.height())

    def _draw_spinner(self, painter: QPainter):
        """Draws an animated spinner centred in the widget"""
        w, h = self.width(), self.height()

        # Dark background
        painter.setBrush(QColor(30, 30, 30))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, w, h)

        # Spinner arc
        margin = 14
        rect_size = min(w, h) - margin * 2

        cx = (w - rect_size) // 2
        cy = (h - rect_size) // 2

        # Faint track circle
        track_pen = QPen(QColor(80, 80, 80), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(cx, cy, rect_size, rect_size)

        # Animated arc (gradient-like via two arcs)
        arc_pen = QPen(QColor(220, 60, 60), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen)

        from PySide6.QtCore import QRect
        rect = QRect(cx, cy, rect_size, rect_size)
        start_angle = (90 - self.spinner_angle) * 16   # Qt uses 1/16th degrees
        span_angle = -270 * 16                          # 270° arc
        painter.drawArc(rect, start_angle, span_angle)

        # Small "PDF" label below the spinner
        painter.setPen(QColor(200, 200, 200))
        font = painter.font()
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(0, h - 6, w, 10, Qt.AlignmentFlag.AlignHCenter, "conversion…")

    def parcourir_dossier(self):
        dossier = QFileDialog.getExistingDirectory(
            self,
            "Select a folder",
            self.config.get("path", ""),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if dossier:
            self.config["path"] = dossier
            self.sauvegarder_config()

    def afficher_menu(self, position):
        menu = QMenu(self)

        high_action = QAction("High", self)
        high_action.triggered.connect(lambda: self.changer_image("high"))
        menu.addAction(high_action)

        medium_action = QAction("Medium", self)
        medium_action.triggered.connect(lambda: self.changer_image("medium"))
        menu.addAction(medium_action)

        low_action = QAction("Low", self)
        low_action.triggered.connect(lambda: self.changer_image("low"))
        menu.addAction(low_action)

        menu.addSeparator()

        parcourir_action = QAction("Browse", self)
        parcourir_action.triggered.connect(self.parcourir_dossier)
        menu.addAction(parcourir_action)

        menu.addSeparator()

        quitter_action = QAction("Quit", self)
        quitter_action.triggered.connect(QApplication.quit)
        menu.addAction(quitter_action)

        menu.exec(self.mapToGlobal(position))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.starting_position = QPoint(event.position().x(), event.position().y())

    def mouseMoveEvent(self, event):
        if hasattr(self, 'starting_position'):
            delta = QPoint(event.position().x() - self.starting_position.x(),
                           event.position().y() - self.starting_position.y())
            self.move(self.x() + delta.x(), self.y() + delta.y())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if hasattr(self, 'starting_position'):
                delattr(self, 'starting_position')

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.pdf'):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            fichier_path = url.toLocalFile()
            if fichier_path.lower().endswith('.pdf'):
                self.compresser_pdf(fichier_path)

    def compresser_pdf(self, fichier_path: str):
        niveau = self.niveau_actuel
        dossier_sortie = self.config.get("path", "")

        if not dossier_sortie:
            dossier_sortie = os.path.dirname(os.path.abspath(__file__))

        nom_fichier = os.path.basename(fichier_path)
        nom_base, _ = os.path.splitext(nom_fichier)

        fichier_entrant = str(Path(fichier_path).absolute())
        fichier_sortie = str(Path(dossier_sortie) / f"{nom_base}.pdf")

        print(f"File compression: {fichier_entrant}")
        print(f"Compression level: {niveau}")
        print(f"Output file: {fichier_sortie}")

        # Start the spinner before launching the thread
        self._start_spinner()

        # Create and configure the worker thread
        thread = ConversionThread(fichier_entrant, fichier_sortie, niveau)
        thread.finished.connect(self._on_conversion_finished)
        thread.error.connect(self._on_conversion_error)

        # Keep a reference so the thread is not garbage-collected
        self._conversion_threads.append(thread)
        thread.start()

    def _on_conversion_finished(self):
        print("Conversion completed.")
        self._stop_spinner()

    def _on_conversion_error(self, message: str):
        print(f"Error while compressing: {message}")
        self._stop_spinner()


# Application entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)

    fenetre = CarreRouge()
    fenetre.show()

    try:
        sys.exit(app.exec())
    except AttributeError:
        sys.exit(app.exec_())