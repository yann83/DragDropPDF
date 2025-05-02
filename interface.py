import sys
import json
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QMenu, QFileDialog
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPainter, QAction, QPixmap, QDragEnterEvent, QDropEvent

from core import GhostConverter
from config import ConfigJson


class CarreRouge(QWidget):
    def __init__(self):
        super().__init__()

        config_json = ConfigJson(Path("config.json"))
        self.config_json_path = config_json.determine_config_path()

        # Loading the configuration
        self.config = self.charger_config()

        # Window configuration
        self.setWindowTitle("DropPDF")  # window title
        self.setFixedSize(100, 100)  # Fixed size of 100x100 pixels

        # Remove window borders and force foreground
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # Removing borders
            Qt.WindowType.WindowStaysOnTopHint  # Window always in the foreground
        )

        # Allow mouse tracking for right click
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.afficher_menu)

        # Position the square in the bottom right corner of the screen, 100 pixels from the edge
        # Get the screen dimensions
        screen_rect = QApplication.primaryScreen().geometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()

        # Calculate position (bottom right 100 pixels from edge)
        pos_x = screen_width - self.width() - 100
        pos_y = screen_height - self.height() - 100

        # Apply position
        self.move(pos_x, pos_y)

        # Determine current level and image from configuration
        self.niveau_actuel = next(iter(self.config["current"].keys()))
        self.image_actuelle = self.config["current"][self.niveau_actuel]
        #print(f"Actual level: {self.niveau_actuel}, Image: {self.image_actuelle}")

        # Build the full path of the image
        chemin_image = os.path.join("img", self.image_actuelle)
        # Load image if it exists
        if os.path.exists(chemin_image):
            self.pixmap = QPixmap(chemin_image)
            #print(f"Image loaded: {chemin_image}")
        else:
            self.pixmap = None
            #print(f"Image not found: {chemin_image}")

        # Enable drag and drop
        self.setAcceptDrops(True)

    def charger_config(self):
        """
        Loads the configuration from the config.json file
        """
        try:
            with open(self.config_json_path, "r") as fichier:
                return json.load(fichier)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            #print(f"error loading configuration: {e}")
            # Default configuration in case of error
            return {
                "path": "",
                "pics": {"high": "pdf.jpg", "medium": "pdflow.jpg", "low": "pdfmedium.jpg"},
                "current": {"medium": "pdflow.jpg"}
            }

    def sauvegarder_config(self):
        """
        Save the configuration to the config.json file
        """
        try:
            with open(self.config_json_path, "w") as fichier:
                json.dump(self.config, fichier, indent=2)
            #print("Configuration saved successfully")
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def changer_image(self, niveau):
        """
        Changes the current image according to the chosen level (high, medium, low)
        """
        if niveau in self.config["pics"]:
            # Update current level
            self.niveau_actuel = niveau

            # Retrieve the image name for this level
            image_nom = self.config["pics"][niveau]
            self.image_actuelle = image_nom

            # Update the configuration
            self.config["current"] = {niveau: image_nom}

            # Save configuration
            self.sauvegarder_config()

            # Build the full path of the image
            chemin_image = os.path.join("img", image_nom)

            # Load the new image if it exists
            if os.path.exists(chemin_image):
                self.pixmap = QPixmap(chemin_image)
                #print(f"Image changed to: {niveau} ({chemin_image})")
            else:
                self.pixmap = None
                #print(f"Image not found: {chemin_image}")

            # Redraw the widget
            self.update()

    def paintEvent(self, event):
        """
        Method called automatically to draw the window contents
        """
        peintre = QPainter(self)

        if self.pixmap and not self.pixmap.isNull():
            # Draw the image if available
            peintre.drawPixmap(0, 0, self.width(), self.height(), self.pixmap)
        else:
            # Otherwise, draw a red square by default
            peintre.setBrush(QColor(255, 0, 0))  # Red in RGB
            peintre.drawRect(0, 0, self.width(), self.height())

    def parcourir_dossier(self):
        """
        Opens a dialog box to choose a folder and updates the configuration
        """
        dossier = QFileDialog.getExistingDirectory(
            self,
            "Select a folder",
            self.config.get("path", ""),  # Initial folder based on config
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        # If the user selected a folder (did not cancel)
        if dossier:
            #print(f"Selected folder: {dossier}")

            # Update the value in the configuration
            self.config["path"] = dossier

            # Save configuration
            self.sauvegarder_config()

    def afficher_menu(self, position):
        """
        Displays the context menu at the right-click position
        """
        menu = QMenu(self)

        # Add high, medium, low options
        high_action = QAction("High", self)
        high_action.triggered.connect(lambda: self.changer_image("high"))
        menu.addAction(high_action)

        medium_action = QAction("Medium", self)
        medium_action.triggered.connect(lambda: self.changer_image("medium"))
        menu.addAction(medium_action)

        low_action = QAction("Low", self)
        low_action.triggered.connect(lambda: self.changer_image("low"))
        menu.addAction(low_action)

        # Add a separator
        menu.addSeparator()

        # Add the "Browse" option
        parcourir_action = QAction("Browse", self)
        parcourir_action.triggered.connect(self.parcourir_dossier)
        menu.addAction(parcourir_action)

        # Add a separator
        menu.addSeparator()

        # Add "Exit" option to the menu
        quitter_action = QAction("Quit", self)
        quitter_action.triggered.connect(QApplication.quit)
        menu.addAction(quitter_action)

        # Show menu at click position
        menu.exec(self.mapToGlobal(position))

    def mousePressEvent(self, event):
        """
        Handles mouse click events
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # Save the starting position to enable movement
            self.starting_position = QPoint(event.position().x(), event.position().y())

    def mouseMoveEvent(self, event):
        """
        Handles mouse movement events
        """
        if hasattr(self, 'starting_position'):
            # Calculate the displacement from the initial position
            delta = QPoint(event.position().x() - self.starting_position.x(),
                           event.position().y() - self.starting_position.y())

            # move the window
            self.move(self.x() + delta.x(), self.y() + delta.y())

    def mouseReleaseEvent(self, event):
        """
        Handles mouse button release events
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # Remove reference to starting position
            if hasattr(self, 'starting_position'):
                delattr(self, 'starting_position')

    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Handles drag and drop events - accepts the event if it is a PDF file
        """
        if event.mimeData().hasUrls():
            # Check if at least one of the files is a PDF
            for url in event.mimeData().urls():
                fichier_path = url.toLocalFile()
                if fichier_path.lower().endswith('.pdf'):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent):
        """
        Gère l'événement de dépôt de fichier
        """
        # Retrieve URLs of uploaded files
        for url in event.mimeData().urls():
            fichier_path = url.toLocalFile()

            # Process only PDF files
            if fichier_path.lower().endswith('.pdf'):
                self.compresser_pdf(fichier_path)

    def compresser_pdf(self, fichier_path: str):
        """
        Compress a PDF file placed on the square
        """
        # Retrieve current level (high, medium, low)
        niveau = self.niveau_actuel

        # Retrieve output folder from configuration
        dossier_sortie = self.config.get("path", "")

        # If the output folder is empty, use the script folder
        if not dossier_sortie:
            dossier_sortie = os.path.dirname(os.path.abspath(__file__))

        # Extract file name
        nom_fichier = os.path.basename(fichier_path)
        nom_base, _ = os.path.splitext(nom_fichier)

        # Generate the output filename
        # Use Path to properly manage Windows paths
        fichier_entrant = str(Path(fichier_path).absolute())
        fichier_sortie = str(Path(dossier_sortie) / f"{nom_base}.pdf")

        #print(f"File compression: {fichier_entrant}")
        #print(f"Compression level: {niveau}")
        #print(f"Output file: {fichier_sortie}")

        try:
            # Create an instance of GhostConverter
            converter = GhostConverter(fichier_path, fichier_sortie, niveau)

            # Start compression
            converter.launch()

            #print(f"Compression completed: {fichier_sortie}")
        except Exception as e:
            print(f"Error while compressing: {e}")


# Application entry point
if __name__ == "__main__":
    #print("Starting the application...")

    # Create the application
    app = QApplication(sys.argv)

    # Create and display our custom widget
    fenetre = CarreRouge()
    fenetre.show()

    #print("Window displayed")

    # Start the main event loop
    try:
        sys.exit(app.exec())
    except AttributeError:
        # For older versions of PySide6
        sys.exit(app.exec_())