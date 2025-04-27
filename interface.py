import sys
import json
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QMenu, QFileDialog
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPainter, QAction, QPixmap, QDragEnterEvent, QDropEvent

from core import GhostConverter


class CarreRouge(QWidget):
    def __init__(self):
        super().__init__()

        # Chargement de la configuration
        self.config = self.charger_config()

        # Configuration de la fenêtre
        self.setWindowTitle("DropPDF")  # Titre de la fenêtre
        self.setFixedSize(100, 100)  # Taille fixe de 100x100 pixels

        # Supprimer les bordures de la fenêtre et forcer le premier plan
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # Suppression des bordures
            Qt.WindowType.WindowStaysOnTopHint  # Fenêtre toujours au premier plan
        )

        # Autoriser le suivi de la souris pour le clic droit
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.afficher_menu)

        # Positionner le carré en bas à droite de l'écran, à 100 pixels du bord
        # Obtenir les dimensions de l'écran
        screen_rect = QApplication.primaryScreen().geometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()

        # Calculer la position (bas droite à 100 pixels du bord)
        pos_x = screen_width - self.width() - 100
        pos_y = screen_height - self.height() - 100

        # Appliquer la position
        self.move(pos_x, pos_y)

        # Déterminer le niveau et l'image actuels à partir de la configuration
        self.niveau_actuel = next(iter(self.config["current"].keys()))
        self.image_actuelle = self.config["current"][self.niveau_actuel]
        print(f"Niveau actuel: {self.niveau_actuel}, Image: {self.image_actuelle}")

        # Construire le chemin complet de l'image
        chemin_image = os.path.join("img", self.image_actuelle)
        # Charger l'image si elle existe
        if os.path.exists(chemin_image):
            self.pixmap = QPixmap(chemin_image)
            print(f"Image chargée: {chemin_image}")
        else:
            self.pixmap = None
            print(f"Image non trouvée: {chemin_image}")

        # Activer le glisser-déposer
        self.setAcceptDrops(True)

    def charger_config(self):
        """Charge la configuration depuis le fichier config.json"""
        try:
            with open("config.json", "r") as fichier:
                return json.load(fichier)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
            # Configuration par défaut en cas d'erreur
            return {
                "path": "",
                "pics": {"high": "pdf.jpg", "medium": "pdflow.jpg", "low": "pdfmedium.jpg"},
                "current": {"medium": "pdflow.jpg"}
            }

    def sauvegarder_config(self):
        """Sauvegarde la configuration dans le fichier config.json"""
        try:
            with open("config.json", "w") as fichier:
                json.dump(self.config, fichier, indent=2)
            print("Configuration sauvegardée avec succès")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")

    def changer_image(self, niveau):
        """Change l'image actuelle selon le niveau choisi (high, medium, low)"""
        if niveau in self.config["pics"]:
            # Mettre à jour le niveau actuel
            self.niveau_actuel = niveau

            # Récupérer le nom de l'image pour ce niveau
            image_nom = self.config["pics"][niveau]
            self.image_actuelle = image_nom

            # Mettre à jour la configuration
            self.config["current"] = {niveau: image_nom}

            # Sauvegarder la configuration
            self.sauvegarder_config()

            # Construire le chemin complet de l'image
            chemin_image = os.path.join("img", image_nom)

            # Charger la nouvelle image si elle existe
            if os.path.exists(chemin_image):
                self.pixmap = QPixmap(chemin_image)
                print(f"Image changée pour: {niveau} ({chemin_image})")
            else:
                self.pixmap = None
                print(f"Image non trouvée: {chemin_image}")

            # Redessiner le widget
            self.update()

    def paintEvent(self, event):
        """Méthode appelée automatiquement pour dessiner le contenu de la fenêtre"""
        peintre = QPainter(self)

        if self.pixmap and not self.pixmap.isNull():
            # Dessiner l'image si disponible
            peintre.drawPixmap(0, 0, self.width(), self.height(), self.pixmap)
        else:
            # Sinon, dessiner un carré rouge par défaut
            peintre.setBrush(QColor(255, 0, 0))  # Rouge en RGB
            peintre.drawRect(0, 0, self.width(), self.height())

    def parcourir_dossier(self):
        """Ouvre une boîte de dialogue pour choisir un dossier et met à jour la configuration"""
        dossier = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner un dossier",
            self.config.get("path", ""),  # Dossier initial basé sur la config
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        # Si l'utilisateur a sélectionné un dossier (n'a pas annulé)
        if dossier:
            print(f"Dossier sélectionné: {dossier}")

            # Mettre à jour la valeur dans la configuration
            self.config["path"] = dossier

            # Sauvegarder la configuration
            self.sauvegarder_config()

    def afficher_menu(self, position):
        """Affiche le menu contextuel à la position du clic droit"""
        menu = QMenu(self)

        # Ajouter les options high, medium, low
        high_action = QAction("High", self)
        high_action.triggered.connect(lambda: self.changer_image("high"))
        menu.addAction(high_action)

        medium_action = QAction("Medium", self)
        medium_action.triggered.connect(lambda: self.changer_image("medium"))
        menu.addAction(medium_action)

        low_action = QAction("Low", self)
        low_action.triggered.connect(lambda: self.changer_image("low"))
        menu.addAction(low_action)

        # Ajouter un séparateur
        menu.addSeparator()

        # Ajouter l'option "Parcourir"
        parcourir_action = QAction("Parcourir", self)
        parcourir_action.triggered.connect(self.parcourir_dossier)
        menu.addAction(parcourir_action)

        # Ajouter un séparateur
        menu.addSeparator()

        # Ajouter l'option "Quitter" au menu
        quitter_action = QAction("Quitter", self)
        quitter_action.triggered.connect(QApplication.quit)
        menu.addAction(quitter_action)

        # Afficher le menu à la position du clic
        menu.exec(self.mapToGlobal(position))

    def mousePressEvent(self, event):
        """Gère les événements de clic de souris"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Enregistrer la position de départ pour permettre le déplacement
            self.position_depart = QPoint(event.position().x(), event.position().y())

    def mouseMoveEvent(self, event):
        """Gère les événements de déplacement de la souris"""
        if hasattr(self, 'position_depart'):
            # Calculer le déplacement depuis la position initiale
            delta = QPoint(event.position().x() - self.position_depart.x(),
                           event.position().y() - self.position_depart.y())

            # Déplacer la fenêtre
            self.move(self.x() + delta.x(), self.y() + delta.y())

    def mouseReleaseEvent(self, event):
        """Gère les événements de relâchement du bouton de la souris"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Supprimer la référence à la position de départ
            if hasattr(self, 'position_depart'):
                delattr(self, 'position_depart')

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Gère les événements de glisser-déposer - accepte l'événement si c'est un fichier PDF"""
        if event.mimeData().hasUrls():
            # Vérifier si au moins un des fichiers est un PDF
            for url in event.mimeData().urls():
                fichier_path = url.toLocalFile()
                if fichier_path.lower().endswith('.pdf'):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent):
        """Gère l'événement de dépôt de fichier"""
        # Récupérer les URLs des fichiers déposés
        for url in event.mimeData().urls():
            fichier_path = url.toLocalFile()

            # Traiter uniquement les fichiers PDF
            if fichier_path.lower().endswith('.pdf'):
                self.compresser_pdf(fichier_path)

    def compresser_pdf(self, fichier_path: str):
        """Compresse un fichier PDF déposé sur le carré"""
        # Récupérer le niveau actuel (high, medium, low)
        niveau = self.niveau_actuel

        # Récupérer le dossier de sortie depuis la configuration
        dossier_sortie = self.config.get("path", "")

        # Si le dossier de sortie est vide, utiliser le dossier du script
        if not dossier_sortie:
            dossier_sortie = os.path.dirname(os.path.abspath(__file__))

        # Extraire le nom du fichier
        nom_fichier = os.path.basename(fichier_path)
        nom_base, _ = os.path.splitext(nom_fichier)

        # Générer le nom du fichier de sortie
        # Utiliser Path pour gérer correctement les chemins Windows
        fichier_entrant = str(Path(fichier_path).absolute())
        fichier_sortie = str(Path(dossier_sortie) / f"{nom_base}.pdf")

        print(f"Compression du fichier: {fichier_entrant}")
        print(f"Niveau de compression: {niveau}")
        print(f"Fichier de sortie: {fichier_sortie}")

        try:
            # Créer une instance de GhostConverter
            converter = GhostConverter(fichier_path, fichier_sortie, niveau)

            # Lancer la compression
            converter.launch()

            print(f"Compression terminée: {fichier_sortie}")
        except Exception as e:
            print(f"Erreur lors de la compression: {e}")


# Point d'entrée de l'application
if __name__ == "__main__":
    print("Démarrage de l'application...")

    # Créer l'application
    app = QApplication(sys.argv)

    # Créer et afficher notre widget personnalisé
    fenetre = CarreRouge()
    fenetre.show()

    print("Fenêtre affichée")

    # Lancer la boucle d'événements principale
    try:
        sys.exit(app.exec())
    except AttributeError:
        # Pour les versions plus anciennes de PySide6
        sys.exit(app.exec_())