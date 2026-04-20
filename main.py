from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import QDate
from home_view import HomeView
from settings_view import SettingsView
from statistics_view import StatisticsView
from styles import STYLE
from datetime import datetime, timedelta
import trainer


#dla Windows
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

class TrainerThread(QThread):
    finished = pyqtSignal(int)  # liczba powtórzeń
    def run(self):
        reps = trainer.main()
        self.finished.emit(reps)

class App(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Cyber Trener")
        self.setStyleSheet(STYLE)

        main=QHBoxLayout()#poziomo

        menu=QVBoxLayout()#pionowo
        menu.setSpacing(10)
        menu.setContentsMargins(10, 20, 10, 20)

        self.button_home=QPushButton("Strona główna")
        self.button_statics=QPushButton("Statystyki")
        self.button_settings=QPushButton("Ustawienia")
        self.button_close=QPushButton("Zakończ")

        self.menu_buttons=[self.button_home, self.button_statics, self.button_settings]

        for button in self.menu_buttons + [self.button_close]:
            button.setObjectName("menu_button")
            menu.addWidget(button)

        menu.addStretch()
        self.button_close.clicked.connect(self.close_app)
        menu_widget=QWidget()
        menu_widget.setLayout(menu)


        self.stack=QStackedLayout()
        self.home = HomeView()
        self.home.start_btn.clicked.connect(self.start_training)
        self.stats=StatisticsView()
        self.settings=SettingsView()
        self.settings.save_btn.clicked.connect(self.save_and_go_home)

        self.stack.addWidget(self.home)      # 0
        self.stack.addWidget(self.stats)     # 1
        self.stack.addWidget(self.settings)  # 2


        self.button_home.clicked.connect(lambda: self.change_page(0, self.button_home))
        self.button_statics.clicked.connect(lambda: self.change_page(1, self.button_statics))
        self.button_settings.clicked.connect(lambda: self.change_page(2, self.button_settings))

        container=QWidget()
        container.setLayout(self.stack)

        main.addWidget(menu_widget)
        main.addWidget(container)

        self.setLayout(main)

        self.training_data={
            "2026-04-19": 13,
            "2026-04-15": 5,
            "2026-04-09": 14,
            "2026-04-05": 7,
            "2026-04-04": 2,
            "2026-04-01": 4,
        }

        self.refresh_ui()

        training_days = [
            QDate.fromString(d, "yyyy-MM-dd")
            for d in self.training_data.keys()
        ]

        self.stats.set_training_days(training_days)
        self.home.set_training_days(training_days)

        self.set_active(self.button_home)

    def change_page(self, index, button):
        self.stack.setCurrentIndex(index)
        self.set_active(button)

    def start_training(self):
        self.trainer_thread = TrainerThread()
        self.trainer_thread.finished.connect(self.training_finished)
        self.trainer_thread.start()

    def set_active(self, btn):
        for b in self.menu_buttons:
            b.setProperty("active", False)
            b.style().unpolish(b)
            b.style().polish(b)

        btn.setProperty("active", True)
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def refresh_ui(self):
        day, week, month = self.calculate_stats()
        self.stats.update_stats(day, week, month)

        week_data = self.get_week_chart_data()
        self.stats.chart.update_chart(week_data)

    def save_and_go_home(self):
        name = self.settings.name_input.text()
        age = self.settings.age_input.text()
        height = self.settings.height_input.text()
        weight = self.settings.weight_input.text()

        if not name:
            QMessageBox.warning(self, "Błąd", "Podaj imię")
            return

        if not age or not age.isdigit():
            QMessageBox.warning(self, "Błąd", "Wiek musi być liczbą")
            return

        if not height or not height.isdigit():
            QMessageBox.warning(self, "Błąd", "Wzrost musi być liczbą")
            return

        if not weight or not weight.isdigit():
            QMessageBox.warning(self, "Błąd", "Waga musi być liczbą")
            return

        age=int(age)
        height=int(height)
        weight=int(weight)

        if age<0 or age>100:
            QMessageBox.warning(self, "Błąd", "Wiek musi być w zakresie 0–100")
            return

        if height<50 or height>250:
            QMessageBox.warning(self, "Błąd", "Wzrost musi być w zakresie 50–250 cm")
            return

        if weight<40 or weight>150:
            QMessageBox.warning(self, "Błąd", "Waga musi być w zakresie 40–150 kg")
            return

        self.home.update_user(name, age, height, weight)
        self.change_page(0, self.button_home)

    def calculate_stats(self):
        today=datetime.today().date()

        day_sum=0
        week_sum=0
        month_sum=0

        for date_str, reps in self.training_data.items():
            d=datetime.strptime(date_str, "%Y-%m-%d").date()

            if d==today:
                day_sum+=reps

            if today-timedelta(days=7)<=d<=today:
                week_sum+=reps

            if d.month==today.month and d.year==today.year:
                month_sum+=reps

        return day_sum, week_sum, month_sum

    def training_finished(self, reps):
        today = datetime.today().strftime("%Y-%m-%d")
        if today in self.training_data:
            self.training_data[today] += reps
        else:
            self.training_data[today] = reps
        self.refresh_ui()
        QMessageBox.information(
            self,
            "Trening zakończony",
            f"Wykonałaś {reps} powtórzeń 💪"

        )

    def get_week_chart_data(self):
        today=datetime.today().date()
        start=today-timedelta(days=today.weekday())
        week=[]

        for i in range(7):
            day=start+timedelta(days=i)
            key=day.strftime("%Y-%m-%d")
            week.append(self.training_data.get(key, 0))
        return week


    def close_app(self):
        reply=QMessageBox.question(
            self,
            "Zamknąć aplikację",
            "Czy na pewno chcesz zakończyć?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply==QMessageBox.Yes:
            QApplication.quit()


app=QApplication([])
app.setFont(QFont("Arial", 11))
window=App()

screen=QApplication.primaryScreen()
size=screen.size()
window.resize(int(size.width()*0.8), int(size.height()*0.8))
window.show()
app.exec_()