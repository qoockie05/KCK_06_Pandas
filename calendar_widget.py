from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPainter, QColor


MONTHS_PL = {
    1: "Styczeń", 2: "Luty", 3: "Marzec", 4: "Kwiecień",
    5: "Maj", 6: "Czerwiec", 7: "Lipiec", 8: "Sierpień",
    9: "Wrzesień", 10: "Październik", 11: "Listopad", 12: "Grudzień"
}

class CalendarGrid(QCalendarWidget):
    BG_COLOR=QColor("#020617")
    WEEKEND_COLOR=QColor("red")
    WEEKDAY_COLOR=QColor("white")
    TRAINING_COLOR=QColor("#ff4d8d")

    def __init__(self):
        super().__init__()
        self.setGridVisible(False)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)#numer tygodnia
        self.setHorizontalHeaderFormat(QCalendarWidget.NoHorizontalHeader)#nazwa dnia
        self.setNavigationBarVisible(False)
        self.setFocusPolicy(Qt.NoFocus)#dziejszy dzien
        self.training_days = set()
        self.setStyleSheet("""
            QTableView {
                background-color: #020617;
                border: none;
            }
        """)

    def set_training_days(self, days):
        self.training_days=set(days)
        self.update()

    def paintCell(self, painter: QPainter, rect, date):
        painter.save()

        if date.month()!=self.monthShown():
            painter.restore()
            return

        painter.fillRect(rect,self.BG_COLOR)

        color=self.WEEKEND_COLOR\
            if date.dayOfWeek()>=6\
            else self.WEEKDAY_COLOR
        painter.setPen(color)

        if date in self.training_days:
            painter.setRenderHint(QPainter.Antialiasing)

            size=min(rect.width(),rect.height())-12

            x=rect.center().x()-size/2
            y=rect.center().y()-size/2

            painter.setBrush(self.TRAINING_COLOR)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x),int(y),int(size),int(size))
            painter.setPen(QColor("black"))

        painter.drawText(rect,Qt.AlignCenter,str(date.day()))
        painter.restore()

class CustomCalendar(QWidget):
    def __init__(self):
        super().__init__()
        layout=QVBoxLayout() #pionowo
        header=QHBoxLayout()#naglowek poziommo

        self.prev_button=QPushButton("⬅")
        self.next_button=QPushButton("➡")

        self.prev_button.setObjectName("arrow_button")
        self.next_button.setObjectName("arrow_button")

        self.month_label=QLabel()
        self.month_label.setAlignment(Qt.AlignCenter)
        self.month_label.setStyleSheet("font-size:18px; font-weight:bold;")

        header.addWidget(self.prev_button)
        header.addWidget(self.month_label)
        header.addWidget(self.next_button)


        days_layout=QHBoxLayout()
        for day in ["Pon","Wt","Śr","Czw","Pt","Sob","Nd"]:
            label=QLabel(day)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color:red;"
                                if day in ["Sob","Nd"]
                                else "color:#94a3b8;")
            days_layout.addWidget(label)

        self.calendar=CalendarGrid()
        self.calendar.setFixedSize(260, 260)

        self.prev_button.clicked.connect(self.prev_month)
        self.next_button.clicked.connect(self.next_month)

        layout.addLayout(header)
        layout.addLayout(days_layout)
        layout.addWidget(self.calendar, alignment=Qt.AlignCenter)
        self.setLayout(layout)
        self.update_month_label()

    def update_month_label(self):
        m=self.calendar.monthShown()
        y=self.calendar.yearShown()
        self.month_label.setText(f"{MONTHS_PL[m]} {y}")

    def next_month(self):
        self.calendar.showNextMonth()
        self.update_month_label()

    def prev_month(self):
        self.calendar.showPreviousMonth()
        self.update_month_label()

    def set_training_days(self, days):
        self.calendar.set_training_days(days)