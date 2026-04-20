from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()

        main=QVBoxLayout()#pionowo
        main.setAlignment(Qt.AlignCenter)

        card=QFrame()
        card.setObjectName("card")
        card.setFixedWidth(350)

        layout=QVBoxLayout()#pionowo

        title=QLabel("<h2>Ustawienia</h2>")
        title.setAlignment(Qt.AlignCenter)

        form=QFormLayout()
        form.setSpacing(15)

        self.name_input=QLineEdit()
        self.age_input=QLineEdit()
        self.height_input=QLineEdit()
        self.weight_input=QLineEdit()

        self.age_input.setValidator(QIntValidator(0, 100))
        self.height_input.setValidator(QIntValidator(50, 250))
        self.weight_input.setValidator(QIntValidator(40, 150))

        for inp in [self.name_input, self.age_input, self.height_input, self.weight_input]:
            inp.setObjectName("settings_label")

        form.addRow("Imię:", self.name_input)
        form.addRow("Wiek:", self.age_input)
        form.addRow("Wzrost (cm):", self.height_input)
        form.addRow("Waga (kg):", self.weight_input)

        self.save_btn = QPushButton("Zapisz")
        self.save_btn.setObjectName("start_button")

        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addLayout(form)
        layout.addSpacing(20)
        layout.addWidget(self.save_btn)

        card.setLayout(layout)

        main.addWidget(card)
        self.setLayout(main)