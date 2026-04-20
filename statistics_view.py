from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from calendar_widget import CustomCalendar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class StatsCard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout()#pionowo

        self.title=QLabel(f"<b>{title}</b>")
        self.title.setAlignment(Qt.AlignCenter)

        self.value=QLabel("0")
        self.value.setAlignment(Qt.AlignCenter)
        self.value.setStyleSheet("font-size:34px; color:#ff4d8d; font-weight:bold;")

        subtitle=QLabel("powtórzeń")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color:#94a3b8;")

        layout.addWidget(self.title)
        layout.addSpacing(5)
        layout.addWidget(self.value)
        layout.addWidget(subtitle)

        self.setLayout(layout)

    def set_value(self, val):
        self.value.setText(str(val))


class WeeklyChart(FigureCanvas):
    def __init__(self):
        self.fig=Figure(figsize=(4, 2.5))
        super().__init__(self.fig)

        self.ax=self.fig.add_subplot(111)#rzad,kolumna,wykres
        self.setStyleSheet("background-color: transparent;")

    def update_chart(self, data):
        self.ax.clear()

        days=["Pn", "Wt", "Śr", "Cz", "Pt", "Sb", "Nd"]

        line,=self.ax.plot(days, data, marker='o')
        line.set_color("#ff4d8d")
        line.set_linewidth(2)


        self.ax.set_facecolor("#1c1c1c")#tlo obszar wykresu
        self.fig.patch.set_facecolor("#1c1c1c")#cale tlo

        max_val=max(data)\
            if data\
            else 10
        self.ax.set_ylim(-1, max_val + 2)

        step=4
        self.ax.set_yticks(list(range(0, max_val + step, step)))

        self.ax.tick_params(colors="white")#color tekstu

        for spine in self.ax.spines.values():
            spine.set_color("#444")#kolor krawedzi

        self.fig.subplots_adjust(left=0.18, right=0.95, bottom=0.30, top=0.85)

        self.draw()


class StatisticsView(QWidget):
    def __init__(self):
        super().__init__()

        main=QHBoxLayout()#poziomo
        main.setSpacing(20)

        #srodkowa kolumna
        left=QVBoxLayout()
        left.setAlignment(Qt.AlignTop)

        title=QLabel("<h2>Statystyki</h2>")
        title.setAlignment(Qt.AlignCenter)

        self.day_card=StatsCard("Dzisiaj")
        self.week_card=StatsCard("Ten tydzień")
        self.month_card=StatsCard("Ten miesiąc")

        left.addWidget(title)
        left.addSpacing(20)
        left.addWidget(self.day_card)
        left.addWidget(self.week_card)
        left.addWidget(self.month_card)
        left.addStretch()


        right=QVBoxLayout()
        right.setAlignment(Qt.AlignTop)
        right.setSpacing(15)

        calendar_card=QFrame()
        calendar_card.setObjectName("card")
        cal_layout=QVBoxLayout()


        self.calendar=CustomCalendar()
        cal_layout.addSpacing(10)
        cal_layout.addWidget(self.calendar, alignment=Qt.AlignCenter)
        calendar_card.setLayout(cal_layout)


        chart_card=QFrame()
        chart_card.setObjectName("card")
        chart_layout=QVBoxLayout()
        chart_title=QLabel("<b>Tydzień</b>")
        chart_title.setAlignment(Qt.AlignCenter)

        self.chart=WeeklyChart()
        chart_layout.addWidget(chart_title)
        chart_layout.addSpacing(10)
        chart_layout.addWidget(self.chart)

        chart_card.setLayout(chart_layout)

        #prawa kolumna
        right.addWidget(calendar_card)
        right.addWidget(chart_card)
        right.addStretch()


        main.addLayout(left, 2)
        main.addLayout(right, 1)

        self.setLayout(main)


    def update_stats(self, day, week, month):
        self.day_card.set_value(day)
        self.week_card.set_value(week)
        self.month_card.set_value(month)

    def set_training_days(self, days):
        self.calendar.set_training_days(days)