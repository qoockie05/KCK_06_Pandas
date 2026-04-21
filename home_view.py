from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from calendar_widget import CustomCalendar
import random

class HomeView(QWidget):
    def __init__(self):
        super().__init__()
        main=QHBoxLayout()

        #srodkowa kolumna
        center=QVBoxLayout()#pionowo
        self.greeting_label=QLabel("<h2>Hej Alicja 👋</h2>")
        subtitle=QLabel("<span style='color:#94a3b8'>To będzie dobry dzień!</span>")

        self.start_btn=QPushButton("▶ Zacznij trening")
        self.start_btn.setObjectName("start_button")

        center.addWidget(self.greeting_label)
        center.addWidget(subtitle)
        center.addSpacing(40)
        center.addWidget(self.start_btn)
        center.addStretch()

        center_widget=QWidget()
        center_widget.setLayout(center)

        #prawa kolumna
        right=QVBoxLayout()#pionowo

        profile = QFrame()
        profile.setObjectName("card")

        self.profile_label = QLabel(
            "👤 Alicja\nWiek: 25\nWzrost: 170 cm\nWaga: 60 kg"
        )

        p_layout=QVBoxLayout()
        p_layout.addWidget(self.profile_label)
        profile.setLayout(p_layout)


        motivation=QFrame()
        motivation.setObjectName("card")

        quotes=[
            "Małe kroki prowadzą do wielkich zmian.",
            "Nie poddawaj się.",
            "Każdy dzień to nowa szansa."
        ]

        self.motivation_text=QLabel(random.choice(quotes))
        self.motivation_text.setWordWrap(True)
        self.motivation_text.setStyleSheet("color:#94a3b8;")

        m_layout=QVBoxLayout()
        m_layout.addWidget(QLabel("💬 Motywacja"))
        m_layout.addWidget(self.motivation_text)
        motivation.setLayout(m_layout)

        calendar_card=QFrame()
        calendar_card.setObjectName("card")

        cal_layout=QVBoxLayout()

        self.calendar=CustomCalendar()

        cal_layout.addWidget(self.calendar)
        calendar_card.setLayout(cal_layout)

        #prawa kolumna
        right.addWidget(profile)
        right.addWidget(motivation)
        right.addWidget(calendar_card)
        right.addStretch()

        right_widget=QWidget()
        right_widget.setLayout(right)
        right_widget.setFixedWidth(350)

        main.addWidget(center_widget)
        main.addWidget(right_widget)

        self.setLayout(main)


    def update_user(self, name, age, height, weight):
        if name:
            self.greeting_label.setText(f"<h2>Hej {name} 👋</h2>")

        self.profile_label.setText(
            f"👤 {name}\nWiek: {age}\nWzrost: {height} cm\nWaga: {weight} kg"
        )

    def set_training_days(self, days):
        self.calendar.set_training_days(days)