from PySide6.QtCore import QCoreApplication, QTimer, Qt, QRectF, QPropertyAnimation, Property
from PySide6.QtGui import QPainter, QColor, QFont, QPixmap
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QWidget,
                               QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QSplitter,
                               QTabWidget, QComboBox)
import pyqtgraph as pg
import os
import sys
import numpy as np
import time
import threading
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.BluetoothModule import Bluetooth

blutooth_input = None
bluetooth_output = None
bluetooth_send_flag = False
bluetooth_module = Bluetooth()

status_message = '0'
signal = None
index = 12
update_index = False

class QSwitch(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 30)
        self.checked = False
        self._offset = 5
        self.animation = QPropertyAnimation(self, b"offset")
        self.animation.setDuration(200)
        self.setStyleSheet("background: transparent;")

    def mousePressEvent(self, event):
        self.checked = not self.checked
        self.animate()
        super().mousePressEvent(event)

    def animate(self):
        start_value = self._offset
        end_value = 35 if self.checked else 5
        self.animation.stop()
        self.animation.setStartValue(start_value)
        self.animation.setEndValue(end_value)
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg_color = QColor("#FFD700") if self.checked else QColor("#555")
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 60, 30, 15, 15)
        circle_color = QColor("#FFFFFF")
        painter.setBrush(circle_color)
        painter.drawEllipse(self._offset, 5, 20, 20)
        emoji = "🌙" if self.checked else "☀️"
        painter.drawText(20, 22, emoji)
        painter.end()

    def getOffset(self):
        return self._offset

    def setOffset(self, value):
        self._offset = value
        self.update()

    offset = Property(int, getOffset, setOffset)

class SettingsTabWidget(QWidget):
    def __init__(self, parent=None, current_language='tr', dark_mode=True):
        super().__init__(parent)
        self.current_language = current_language
        self.translations = {
            'tr': {
                'language_tab': "Dil",
                'theme_tab': "Tema",
                'language_label': "Dil Seçimi:",
                'theme_label': "Tema Seçimi:",
                'save_button': "Kaydet",
                'cancel_button': "Geri"
            },
            'en': {
                'language_tab': "Language",
                'theme_tab': "Theme",
                'language_label': "Select Language:",
                'theme_label': "Select Theme:",
                'save_button': "Save",
                'cancel_button': "Back"
            }
        }
        layout = QVBoxLayout(self)
        self.tabWidget = QTabWidget()
        #layout.addWidget(self.tabWidget)

        # Dil Sekmesi
        langLayout = QVBoxLayout()
        self.langLabel = QLabel()
        langLayout.addWidget(self.langLabel)
        layout.addLayout(langLayout)
        self.langCombo = QComboBox()
        self.langCombo.addItems(["TR", "EN"])
        self.langCombo.setCurrentText(current_language.upper())
        langLayout.addWidget(self.langCombo)
        langLayout.addStretch(1)

        # Tema Sekmesi
        themeLayout = QVBoxLayout()
        self.themeLabel = QLabel()
        themeLayout.addWidget(self.themeLabel)
        layout.addLayout(themeLayout)
        self.themeSwitch = QSwitch()
        self.themeSwitch.checked = dark_mode
        self.themeSwitch.setOffset(35 if dark_mode else 5)
        themeLayout.addWidget(self.themeSwitch)
        themeLayout.addStretch(1)

        # Alt butonlar
        buttonLayout = QHBoxLayout()
        buttonLayout.setAlignment(Qt.AlignLeft)
        self.cancelButton = QPushButton()
        self.saveButton = QPushButton()
        buttonLayout.addWidget(self.cancelButton)
        buttonLayout.addWidget(self.saveButton)
        layout.addLayout(buttonLayout)

        self.set_language(self.current_language)

    def set_language(self, lang):
        self.current_language = lang
        texts = self.translations[lang]
        self.langLabel.setText(texts['language_label'])
        self.themeLabel.setText(texts['theme_label'])
        self.saveButton.setText(texts['save_button'])
        self.cancelButton.setText(texts['cancel_button'])
        self.tabWidget.setTabText(0, texts['language_tab'])
        self.tabWidget.setTabText(1, texts['theme_tab'])

    def get_settings(self):
        language = self.langCombo.currentText().lower()
        dark_mode = self.themeSwitch.checked
        return language, dark_mode

    def reset_settings(self, current_language, dark_mode):
        self.langCombo.setCurrentText(current_language.upper())
        self.themeSwitch.checked = dark_mode
        self.themeSwitch.setOffset(35 if dark_mode else 5)
        self.set_language(current_language)

class CircularTimer(QWidget):
    def __init__(self, parent=None, max_value=60):
        super().__init__(parent)
        self._progress = 0
        self._max_value = max_value
        self._bg_color = QColor("#00BCD4")
        self._progress_color = QColor("#4A148C")
        self._text_color = QColor("#FFFFFF")
        self._radius = 40
        self.setFixedSize(self._radius * 2, self._radius * 2)

    def setProgress(self, value):
        self._progress = value
        self.update()

    def setMaxValue(self, max_value):
        self._max_value = max_value

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0, 0, self.width(), self.height())
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._bg_color)
        painter.drawEllipse(rect)
        progress_mod = self._progress % self._max_value
        angle_span = int(360 * (progress_mod / self._max_value))
        painter.setBrush(self._progress_color)
        painter.drawPie(rect, 90 * 16, -angle_span * 16)
        painter.setPen(self._text_color)
        font = QFont("Arial", 16, QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, str(int(self._progress)))

class MainWindow(QMainWindow):
    global bluetooth_input

    def __init__(self):
        super().__init__()
        self.current_image_index = 12
        self.setObjectName("MainWindow")
        self.resize(800, 600)

        self.dark_mode = True
        self.current_language = 'tr'

        self.translations = {
            'en': {
                'start_button': "Start Button",
                'stop_button': "Stop Button",
                'settings_button': "Settings",
                'bluetooth_button': "Connect to Bluetooth",
                'timer_button_start': "Start Timer",
                'timer_button_stop': "Stop Timer",
                'w_button': "W",
                'a_button': "A",
                's_button': "S",
                'd_button': "D",
            },
            'tr': {
                'start_button': "Başlatma Butonu",
                'stop_button': "Durdurma Butonu",
                'settings_button': "Ayarlar",
                'bluetooth_button': "Bluetooth'a Bağlan",
                'timer_button_start': "Zamanlayıcıyı Başlat",
                'timer_button_stop': "Zamanlayıcıyı Durdur",
                'w_button': "W",
                'a_button': "A",
                's_button': "S",
                'd_button': "D",
            }
        }

        self.centralTabs = QTabWidget()
        self.centralTabs.tabBar().hide()
        self.setCentralWidget(self.centralTabs)

        self.mainTab = QWidget()
        self.centralTabs.addTab(self.mainTab, "Ana Sayfa")
        self.mainLayout = QHBoxLayout(self.mainTab)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setSpacing(20)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.leftPanel = QWidget(self)
        self.leftLayout = QVBoxLayout(self.leftPanel)
        self.leftLayout.setSpacing(10)

        self.pushButtonStart = QPushButton()
        self.leftLayout.addWidget(self.pushButtonStart)

        self.bluetoothButton = QPushButton()
        self.leftLayout.addWidget(self.bluetoothButton)

        self.pushButtonStop = QPushButton()
        self.leftLayout.addWidget(self.pushButtonStop)

        self.direction_label = QLabel()
        self.direction_label.setFixedSize(100, 100)
        self.direction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "direction_images")
        image_path = os.path.join(image_folder, f"{self.current_image_index}.png")
        self.direction_label.setPixmap(
            QPixmap(image_path)
            .scaled(100, 100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        self.leftLayout.addWidget(self.direction_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.statusLabel = QLabel()
        self.leftLayout.addWidget(self.statusLabel)
        self.statusLabel.setText("")

        self.status_update_timer = QTimer(self)
        self.status_update_timer.timeout.connect(self.update_status_label)
        self.status_update_timer.start(100)

        self.graphWidget_update_timer = QTimer(self)
        self.graphWidget_update_timer.timeout.connect(self.update_graphWidget)
        self.graphWidget_update_timer.start(100)

        self.update_direction_timer = QTimer(self)
        self.update_direction_timer.timeout.connect(self.update_direction)
        self.update_direction_timer.start(100)

        self.leftLayout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.pushButtonW = QPushButton()
        self.leftLayout.addWidget(self.pushButtonW)
        self.pushButtonA = QPushButton()
        self.pushButtonS = QPushButton()
        self.pushButtonD = QPushButton()
        self.movementLayout = QHBoxLayout()
        self.movementLayout.setSpacing(10)
        self.movementLayout.addWidget(self.pushButtonA)
        self.movementLayout.addWidget(self.pushButtonS)
        self.movementLayout.addWidget(self.pushButtonD)
        self.leftLayout.addLayout(self.movementLayout)

        self.circularTimer = CircularTimer(self, max_value=120)
        self.leftLayout.addWidget(self.circularTimer, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.pushButtonTimer = QPushButton()
        self.leftLayout.addWidget(self.pushButtonTimer)

        self.settingsButton = QPushButton()
        self.leftLayout.addWidget(self.settingsButton)
        self.settingsButton.clicked.connect(lambda: self.centralTabs.setCurrentIndex(1))

        self.rightPanel = QWidget(self)
        self.rightLayout = QVBoxLayout(self.rightPanel)
        self.rightLayout.setSpacing(10)

        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setBackground('k')
        self.rightLayout.addWidget(self.graphWidget)

        self.statusLabel = QLabel()
        self.statusLabel.setText("")
        self.statusLabel.setStyleSheet("border: 2px solid black; font-size: 16px;")
        self.statusLabel.setAlignment(Qt.AlignCenter)
        self.rightLayout.addWidget(self.statusLabel)
        self.statusLabel.setStyleSheet("""
    QLabel {
        border: 2px solid #4CAF50;
        border-radius: 10px;
        background-color: #282C34;
        color: white;
        font-size: 16px;
        font-weight: bold;
        padding: 10px;
    }
""")

        self.splitter.addWidget(self.leftPanel)
        self.splitter.addWidget(self.rightPanel)
        self.splitter.setSizes([300, 500])
        self.splitter.setHandleWidth(5)
        self.leftPanel.setMinimumWidth(200)
        self.rightPanel.setMinimumWidth(200)
        self.splitter.setMinimumSize(500, 300)
        self.splitter.setStretchFactor(1, 2)

        self.mainLayout.addWidget(self.splitter)

        self.settingsTab = SettingsTabWidget(current_language=self.current_language, dark_mode=self.dark_mode)
        self.centralTabs.addTab(self.settingsTab, "Ayarlar")
        self.settingsTab.saveButton.clicked.connect(self.apply_settings)
        self.settingsTab.cancelButton.clicked.connect(self.cancel_settings)

        self.click_counter = 0
        self.timer_count = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self.pushButtonStart.clicked.connect(self.start_button)
        self.pushButtonStop.clicked.connect(self.stop_button)
        self.pushButtonTimer.clicked.connect(self.toggle_timer)
        self.bluetoothButton.clicked.connect(self.toggle_bluetooth)
        self.pushButtonW.clicked.connect(self.push_button_W)
        self.pushButtonA.clicked.connect(self.push_button_A)
        self.pushButtonS.clicked.connect(self.push_button_S)
        self.pushButtonD.clicked.connect(self.push_button_D)

        self.bluetooth_connected = False
        self.plot_test_data()

        self.set_language(self.current_language)
        self.set_theme()

    def apply_settings(self):
        language, dark_mode = self.settingsTab.get_settings()
        self.current_language = language
        self.dark_mode = dark_mode
        self.set_language(self.current_language)
        self.set_theme()

    def cancel_settings(self):
        self.settingsTab.reset_settings(self.current_language, self.dark_mode)
        self.centralTabs.setCurrentIndex(0)

    def set_language(self, lang):
        self.pushButtonStart.setText(self.translations[lang]['start_button'])
        self.pushButtonStop.setText(self.translations[lang]['stop_button'])
        self.bluetoothButton.setText(self.translations[lang]['bluetooth_button'])
        self.settingsButton.setText(self.translations[lang]['settings_button'])

        if not self.timer.isActive():
            self.pushButtonTimer.setText(self.translations[lang]['timer_button_start'])
        else:
            self.pushButtonTimer.setText(self.translations[lang]['timer_button_stop'])

        self.pushButtonW.setText(self.translations[lang]['w_button'])
        self.pushButtonA.setText(self.translations[lang]['a_button'])
        self.pushButtonS.setText(self.translations[lang]['s_button'])
        self.pushButtonD.setText(self.translations[lang]['d_button'])
        self.settingsTab.set_language(lang)

    def set_theme(self):
        if self.dark_mode:
            dark_stylesheet = """
            QMainWindow { background-color: #2E2E2E; }
            QWidget { background-color: #2E2E2E; }
            QLabel { color: green; font-size: 14px; }
            QPushButton {
                color: green; font-size: 14px;
                background-color: #3C3F41;
                border: 1px solid #5C5C5C;
                border-radius: 5px; padding: 5px;
            }
            QPushButton:hover { background-color: #4E5254; }
            QSplitter::handle { background-color: #5C5C5C; }
        """
            self.setStyleSheet(dark_stylesheet)
            self.graphWidget.setBackground('k')
            button_style = "color: green; font-size: 14px; background-color: #3C3F41; border: 1px solid #5C5C5C; border-radius: 5px; padding: 5px;"
            combo_style = "color: green; font-size: 14px; background-color: #3C3F41; border: 1px solid #5C5C5C; border-radius: 5px; padding: 5px;"
        else:
            light_stylesheet = """
            QMainWindow { background-color: #F0F0F0; }
            QWidget { background-color: #F0F0F0; }
            QLabel { color: black; font-size: 14px; }
            QPushButton {
                color: black; font-size: 14px;
                background-color: #E0E0E0;
                border: 1px solid #A0A0A0;
                border-radius: 5px; padding: 5px;
            }
            QPushButton:hover { background-color: #D0D0D0; }
            QSplitter::handle { background-color: #A0A0A0; }
        """
            self.setStyleSheet(light_stylesheet)
            self.graphWidget.setBackground('w')
            button_style = "color: black; font-size: 14px; background-color: #E0E0E0; border: 1px solid #A0A0A0; border-radius: 5px; padding: 5px;"
            combo_style = "color: black; font-size: 14px; background-color: #E0E0E0; border: 1px solid #A0A0A0; border-radius: 5px; padding: 5px;"

        self.settingsTab.saveButton.setStyleSheet(button_style)
        self.settingsTab.cancelButton.setStyleSheet(button_style)

        self.settingsTab.langCombo.setStyleSheet(combo_style)

    def update_direction_image(self, image_path: str, new_index: int):
        """Update both image and index tracking"""
        image_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "direction_images")
        image_path = os.path.join(image_folder, f"{new_index}.png")

        pixmap = QPixmap(image_path).scaled(
            self.direction_label.width(),
            self.direction_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.direction_label.setPixmap(pixmap)
        self.current_image_index = new_index

    def toggle_timer(self):
        if self.timer.isActive():
            self.timer.stop()
            self.pushButtonTimer.setText(self.translations[self.current_language]['timer_button_start'])
        else:
            self.timer.start(1000)
            self.pushButtonTimer.setText(self.translations[self.current_language]['timer_button_stop'])

    def update_timer(self):
        self.timer_count += 1
        self.circularTimer.setProgress(self.timer_count)

    def toggle_bluetooth(self):
        bluetooth_module.check_connection()
        if bluetooth_module.connection_flag:
            self.bluetoothButton.setText("Bağlantı Kesiliyor...")
            bluetooth_module.disconnect_server()
            bluetooth_flag = False
            self.bluetoothButton.setText(self.translations[self.current_language]['bluetooth_button'])
        else:
            self.bluetoothButton.setText("Bluetootha Bağlanılıyor...")
            bluetooth_module.connect_server()
            bluetooth_module.check_connection()
            if bluetooth_module.connection_flag:
                bluetooth_flag = True
                self.bluetoothButton.setText("Bağlantıyı Kes")
            else:
                bluetooth_flag = False
                self.bluetoothButton.setText(self.translations[self.current_language]['bluetooth_button'])

    def push_button_W(self):
        global bluetooth_send_flag, bluetooth_output
        print("W basıldı")
        bluetooth_output = "W"
        bluetooth_send_flag = True

    def push_button_A(self):
        global bluetooth_send_flag, bluetooth_output
        print("A basıldı")
        bluetooth_output = "A"
        bluetooth_send_flag = True

    def push_button_S(self):
        global bluetooth_send_flag, bluetooth_output
        print("S basıldı")
        bluetooth_output = "S"
        bluetooth_send_flag = True

    def push_button_D(self):
        global bluetooth_send_flag, bluetooth_output
        print("D basıldı")
        bluetooth_output = "D"
        bluetooth_send_flag = True

    def stop_button(self):
        global bluetooth_send_flag, bluetooth_output
        print("Dur")
        bluetooth_output = "STOP"
        bluetooth_send_flag = True

    def plot_test_data(self):
        t = np.linspace(0, 1.0, 500)
        signal = np.sin(2 * np.pi * 10 * t) + np.sin(2 * np.pi * 20 * t)
        freq = np.fft.fftfreq(len(signal), d=t[1] - t[0])
        spectrum = np.fft.fft(signal)
        magnitude = np.abs(spectrum)
        pen = pg.mkPen(color='g')
        self.graphWidget.plot(freq[:len(freq)//2], magnitude[:len(magnitude)//2], pen=pen, clear=True)

    def start_button(self):
        global bluetooth_send_flag, bluetooth_output
        print("Başladı")
        bluetooth_output = "START"
        bluetooth_send_flag = True

    def update_status_label(self):
        global status_message
        if status_message is not None:
            self.statusLabel.setText(status_message)
            status_message = None

    def update_graphWidget(self):
        global signal
        if signal is not None and len(signal) > 0:
            self.update_plot(signal)
            signal = None

    def update_direction(self):
        global index, update_index
        if update_index is True:
            self.update_direction_image(f"{index}.png", index)
            update_index = False

    def update_plot(self):

        spectrum = np.fft.fftshift(np.fft.fft(signal))
        power_dbm = 10 * np.log10(np.abs(spectrum) ** 2)
        print(f"Power dBm: {power_dbm}")

        freqs = np.fft.fftshift(np.fft.fftfreq(len(signal), d= 1/(2.4e6)))
        freqs = freqs + 433e6

        self.graphWidget.plot(freqs, power_dbm, pen='g', clear=True)

        bluetooth_output = "STOP"
        bluetooth_send_flag = True


def bluetooth_receive_handler_thread(window):
    global bluetooth_module, bluetooth_input, status_message, signal, index, update_index
    while True:
        if bluetooth_module.connection_flag:
            data = bluetooth_module.receive_data()
            if data:
                first_char = data[0].lower()
                data_rest = data[1:]
                if first_char == 's':
                    try:
                        print(data_rest)
                        signal_str = data_rest.strip('[]').replace(',', ' ')
                        signal_str = np.fromstring(signal_str, sep=' ', dtype=np.float32)

                        if len(signal_str) % 2 != 0:
                            signal_str = signal_str[:-1]

                        signal = signal_str.reshape(-1, 2).view(np.complex64).flatten()

                        print("Plot updated with signal data")
                    except Exception as e:
                        print(f"Error parsing signal data: {e}")
                elif first_char == 'f':
                    try:
                        value = int(data_rest)
                        step = value // 60

                        index_ = (12 + step) % 12
                        index = (window.current_image_index + step - 1) % 12 + 1
                        update_index = True

                    except ValueError:
                        print(f"Invalid F value: {data_rest}")
                elif first_char == 'h':
                    try:
                        value = int(data_rest)
                        step = value // 30

                        index = (window.current_image_index + step - 1) % 12 + 1
                        update_index = True
                    except ValueError:
                        print(f"Invalid H command value: {data_rest}")

                    print("half scan")
                elif first_char == 'o':
                    status_message = "olcum almaya baslaniyor"
                    print("Start measuring...")
                elif first_char == 'b':
                    status_message = "en iyi aci hesaplaniyor"
                    print("en iyi aci hesaplaniyor")
                elif first_char == 'm':
                    status_message = "arac sinyal gucunun en yuksek oldugu yone dogru harekete geciyor"
                    print("arac sinyal gucunun en yuksek oldugu yone dogru harekete geciyor")
                elif first_char == 'c':
                    status_message = "istenilen hedefe ulasildi"
                    print("istenilen hedefe ulasildi")
                else:
                    try:
                        bluetooth_input = float(data)
                        print("{:.3e}".format(bluetooth_input))
                    except ValueError:
                        print(f"Invalid data format: {data}")

def bluetooth_send_handler_thread():
    global bluetooth_module, bluetooth_output, bluetooth_send_flag
    while True:
        if bluetooth_module.connection_flag and bluetooth_send_flag:
            bluetooth_module.send_data(bluetooth_output)
            bluetooth_send_flag = False
        time.sleep(0.1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()

    bluetooth_recieve_handler = threading.Thread(
        target=bluetooth_receive_handler_thread,
        args=(window,),
        daemon=True
    )
    bluetooth_recieve_handler.start()

    bluetooth_send_handler = threading.Thread(
        target=bluetooth_send_handler_thread,
        daemon=True
    )
    bluetooth_send_handler.start()

    window.show()
    sys.exit(app.exec())
