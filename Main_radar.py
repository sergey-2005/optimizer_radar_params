import sys
import os
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import PyQt5.QtWidgets as QtWidgets
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QRegExp, QTimer, QSettings
from PyQt5.QtGui import QIntValidator, QRegExpValidator
from Count import convert_to_si, calculate_parameters
import math

def get_resource_path(rel_path):
    """Путь к ресурсам для PyInstaller и отладки."""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, rel_path)

PARAMS = ['f0', 'lambda_', 'Tc', 'B', 'S', 'N', 'Tf', 'Fif', 'vmax', 'dres', 'vres', 'dmax', 'mem']
EDITABLE_PARAMS = ['vmax', 'dmax', 'vres', 'dres', 'f0', 'lambda_', 'Tc', 'B', 'S', 'N', 'Tf', 'Fif']
FOCUS_ORDER = ['dres', 'vres', 'dmax', 'vmax', 'f0', 'lambda_', 'Tc', 'B', 'S', 'N', 'Tf', 'Fif']

def style_plot(fig, dark_mode, texts):
    ax = fig.gca()
    bg_color = '#2e2e2e' if dark_mode else 'white'
    fg_color = '#3e3e3e' if dark_mode else 'white'
    text_color = 'white' if dark_mode else 'black'
    fig.set_facecolor(bg_color)
    ax.set_facecolor(fg_color)
    ax.tick_params(colors=text_color)
    ax.xaxis.label.set_color(text_color)
    ax.yaxis.label.set_color(text_color)
    ax.title.set_color(text_color)
    ax.grid(color='gray')
    ax.set_xlabel(texts['plot_xlabel'])
    ax.set_ylabel(texts['plot_ylabel'])
    ax.set_title(texts['plot_title'])

def draw_empty_plot(canvas, fig, dark_mode, texts):
    fig.clf()
    ax = fig.add_subplot(111)
    ax.plot([0], [0], marker='o')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(True)
    style_plot(fig, dark_mode, texts)
    canvas.draw()

def round_to_three_significant(x):
    if x == 0:
        return 0
    return round(x, -int(math.floor(math.log10(abs(x)))) + 2)

class HelpDialog(QtWidgets.QDialog):
    def __init__(self, parent, texts, lang):
        super().__init__(parent)
        self.setWindowTitle(texts.get("btn_help", "Справка"))
        self.setFixedSize(600, 400)
        layout = QtWidgets.QVBoxLayout(self)
        
        help_text = QtWidgets.QTextEdit()
        help_text.setReadOnly(True)
        
        # Загрузка текста справки из файла Helps.txt
        try:
            with open(get_resource_path("Helps.txt"), 'r', encoding='utf-8') as f:
                help_data = json.load(f)
                help_text.setText(help_data.get(lang, {}).get("help", "Не удалось загрузить справку."))
        except:
            help_text.setText("Не удалось загрузить справку из файла Helps.txt.")
        
        layout.addWidget(help_text)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_H, Qt.Key_R, Qt.Key_Escape):
            self.close()
        super().keyPressEvent(event)

class PrioritiesDialog(QtWidgets.QDialog):
    def __init__(self, parent, texts, priorities):
        super().__init__(parent)
        self.setWindowTitle(texts.get("priorities_window_title", "Приоритеты"))
        self.texts = texts
        self.priorities = priorities
        self.build_ui()

    def build_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        self.frames = []
        for i, params in enumerate(self.priorities):
            frame = QtWidgets.QFrame()
            frame.setFrameShape(QtWidgets.QFrame.Box)
            frame.setFixedWidth(200)
            frame_layout = QtWidgets.QVBoxLayout(frame)
            labels = [QtWidgets.QLabel(self.texts.get(p, p), alignment=Qt.AlignCenter) for p in params]
            for lbl in labels:
                frame_layout.addWidget(lbl)
            frame.mousePressEvent = lambda event, idx=i: self.cycle_column(idx)
            frame.setToolTip("Клик для смены порядка")
            layout.addWidget(frame)
            self.frames.append((frame, labels))
        self.setFixedSize(1050, 200)

    def cycle_column(self, col_idx):
        params = self.priorities[col_idx]
        params.append(params.pop(0))
        self.priorities[col_idx] = params
        _, labels = self.frames[col_idx]
        for lbl, param in zip(labels, params):
            lbl.setText(self.texts.get(param, param))

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_1:
            self.cycle_column(0)
        elif key == Qt.Key_2:
            self.cycle_column(1)
        elif key == Qt.Key_3:
            self.cycle_column(2)
        elif key == Qt.Key_4:
            self.cycle_column(3)
        elif key == Qt.Key_5:
            self.cycle_column(4)
        elif key in (Qt.Key_P, Qt.Key_Z, Qt.Key_Escape):
            self.close()
        else:
            super().keyPressEvent(event)

class LimitsDialog(QtWidgets.QDialog):
    def __init__(self, parent, texts, limits, settings):
        super().__init__(parent)
        self.setWindowTitle(texts.get("limits_window_title", "Ограничения"))
        self.texts = texts
        self.limits = limits
        self.settings = settings
        self.build_ui()

    def build_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        self.frames = []
        self.inputs = {}

        # Разделение параметров на 3 столбца по 4 параметра
        params = ['f0', 'lambda_', 'Tc', 'B', 'S', 'N', 'Tf', 'Fif', 'vmax', 'dres', 'vres', 'dmax']
        units = {
            'f0': 'ГГц', 'lambda_': 'м', 'Tc': 'мс', 'B': 'МГц', 'S': 'ГГц/мкс',
            'N': 'шт', 'Tf': 'с', 'Fif': 'МГц', 'vmax': 'м/с', 'dres': 'м',
            'vres': 'м/с', 'dmax': 'м'
        }
        self.params_grid = [params[:4], params[4:8], params[8:]]  # 3 столбца: [f0, lambda_, Tc, B], [S, N, Tf, Fif], [vmax, dres, vres, dmax]

        float_validator = QRegExpValidator(QRegExp(r'^\d*\.?\d*$'))
        int_validator = QIntValidator()

        for col_params in self.params_grid:
            frame = QtWidgets.QFrame()
            frame.setFrameShape(QtWidgets.QFrame.Box)
            frame.setFixedWidth(210)
            frame_layout = QtWidgets.QVBoxLayout(frame)

            for param in col_params:
                param_layout = QtWidgets.QHBoxLayout()
                label_text = f"{param}, {units[param]}"
                label = QtWidgets.QLabel(label_text, alignment=Qt.AlignLeft)
                param_layout.addWidget(label)

                input_field = QtWidgets.QLineEdit()
                input_field.setFixedWidth(100)
                if param == 'N':
                    input_field.setValidator(int_validator)
                else:
                    input_field.setValidator(float_validator)
                input_field.setText(str(self.limits.get(param, "")))
                input_field.textEdited.connect(lambda text, p=param: self.update_limit(p, text))
                param_layout.addWidget(input_field)
                self.inputs[param] = input_field

                frame_layout.addLayout(param_layout)

            layout.addWidget(frame)
            self.frames.append(frame)

        self.setFixedSize(680, 200)

    def update_limit(self, param, text):
        if text.strip() and text != "0":
            try:
                self.limits[param] = float(text)
            except ValueError:
                self.limits[param] = None
        else:
            self.limits.pop(param, None)
        self.settings.setValue("limits", self.limits)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_L, Qt.Key_D, Qt.Key_Escape):
            self.close()
        elif key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            current = self.focusWidget()
            if current in self.inputs.values():
                # Найти текущую позицию (строка, столбец)
                for col_idx, col_params in enumerate(self.params_grid):
                    if current in [self.inputs[param] for param in col_params]:
                        row_idx = col_params.index([p for p in col_params if self.inputs[p] == current][0])
                        break
                else:
                    return

                # Вычислить новую позицию
                if key == Qt.Key_Up:
                    row_idx = (row_idx - 1) % 4
                elif key == Qt.Key_Down:
                    row_idx = (row_idx + 1) % 4
                elif key == Qt.Key_Left:
                    col_idx = (col_idx - 1) % 3
                elif key == Qt.Key_Right:
                    col_idx = (col_idx + 1) % 3

                # Переместить фокус
                new_param = self.params_grid[col_idx][row_idx]
                self.inputs[new_param].setFocus()
            elif not current or current == self:
                # Если фокус не на поле, установить на первое поле
                self.inputs[self.params_grid[0][0]].setFocus()
            return
        super().keyPressEvent(event)

class RadarApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi(get_resource_path("Visual.ui"), self)
        self.settings = QSettings("xAI", "RadarApp")
        self.lang = self.settings.value("language", "ru")
        self.translations = self.fetch_translations(self.lang)
        self.dark_mode = self.settings.value("theme", "dark") == "dark"
        self.param_history = []
        self.priorities = [
            ["S", "B", "Tc"],
            ["Tf", "N", "Tc"],
            ["Tc", "lambda_", "vmax"],
            ["Tf", "lambda_", "vres"],
            ["Fif", "S", "dmax"]
        ]
        self.limits_dialog = None
        self.priorities_dialog = None
        # Загружаем ограничения из настроек или устанавливаем значения по умолчанию из ТЗ
        default_limits = {
            'Fif': 10,    # 10 МГц (fIF_max)
            'B': 1000,    # 1000 МГц (B_max)
            'S': 1        # 1 ГГц/мкс (S_max)
        }
        self.limits = self.settings.value("limits", default_limits)
        if not isinstance(self.limits, dict):
            self.limits = default_limits

        # Настройка сплиттера
        self.splitter = self.findChild(QtWidgets.QSplitter, "splitter")
        if not self.splitter:
            raise AttributeError("Splitter не найден в UI.")
        screen_width = QtWidgets.QApplication.primaryScreen().size().width()
        min_width = screen_width // 4
        self.left_widget = self.findChild(QtWidgets.QWidget, "left_widget")
        self.plot_container = self.findChild(QtWidgets.QWidget, "plot_container")
        if self.left_widget and self.plot_container:
            self.left_widget.setMinimumWidth(min_width)
            self.plot_container.setMinimumWidth(min_width)
            self.splitter.setCollapsible(0, False)
            self.splitter.setCollapsible(1, False)
            self.splitter.setStretchFactor(0, 1)
            self.splitter.setStretchFactor(1, 1)

        # График
        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)
        self.plot_container.layout().addWidget(self.canvas)

        # Поля ввода
        self.fields = {}
        float_validator = QRegExpValidator(QRegExp(r'^\d*\.?\d*$'))
        int_validator = QIntValidator()
        for param in PARAMS:
            field = self.findChild(QtWidgets.QLineEdit, f"input_{param}")
            if field:
                self.fields[param] = field
                if param == 'N':
                    field.setValidator(int_validator)
                elif param != 'mem':
                    field.setValidator(float_validator)
                if param == 'mem':
                    field.setReadOnly(True)
                field.keyPressEvent = lambda e, p=param: self.handle_field_keypress(e, p)
                field.textEdited.connect(lambda text, p=param: self.update_param_history(p, text))

        # Кнопки очистки
        for param in PARAMS:
            btn = self.findChild(QtWidgets.QPushButton, f"clear_{param}")
            if btn:
                btn.clicked.connect(lambda _, p=param: self.clear_param(p))
                btn.setFocusPolicy(Qt.NoFocus)

        # Основные кнопки
        self.btn_compute = self.findChild(QtWidgets.QPushButton, "btn_calculate")
        self.btn_reset = self.findChild(QtWidgets.QPushButton, "btn_clear_all")
        self.btn_menu = self.findChild(QtWidgets.QPushButton, "btn_menu")
        if self.btn_compute:
            self.btn_compute.clicked.connect(self.compute_params)
            self.btn_compute.setFocusPolicy(Qt.NoFocus)
        if self.btn_reset:
            self.btn_reset.clicked.connect(self.reset_all)
            self.btn_reset.setFocusPolicy(Qt.NoFocus)
        if self.btn_menu:
            menu = QtWidgets.QMenu(self)
            self.act_save = menu.addAction(self.translations.get("btn_save", "Сохранить" if self.lang == "ru" else "Save"))
            self.act_load = menu.addAction(self.translations.get("btn_open", "Открыть" if self.lang == "ru" else "Open"))
            self.act_theme = menu.addAction(self.translations.get("btn_toggle_theme", "Сменить тему" if self.lang == "ru" else "Toggle Theme"))
            self.act_lang = menu.addAction(self.translations.get("btn_change_language", "Сменить язык" if self.lang == "ru" else "Change Language"))
            self.act_priorities = menu.addAction(self.translations.get("btn_priorities", "Приоритеты" if self.lang == "ru" else "Priorities"))
            self.act_limits = menu.addAction(self.translations.get("btn_limits", "Ограничения" if self.lang == "ru" else "Limits"))
            self.act_help = menu.addAction(self.translations.get("btn_help", "Справка" if self.lang == "ru" else "Help"))
            self.btn_menu.setMenu(menu)
            self.btn_menu.setFocusPolicy(Qt.NoFocus)
            self.act_save.triggered.connect(self.save_params)
            self.act_load.triggered.connect(self.load_params)
            self.act_theme.triggered.connect(self.switch_theme)
            self.act_lang.triggered.connect(self.switch_language)
            self.act_priorities.triggered.connect(self.toggle_priorities)
            self.act_limits.triggered.connect(self.toggle_limits)
            self.act_help.triggered.connect(self.show_help)

        # Стили
        self.apply_theme("dark" if self.dark_mode else "light")
        self.splitter.setSizes([min_width, min_width * 2])

        # Ошибки
        self.error_display = QtWidgets.QLabel(self)
        self.error_display.setObjectName("error_label")
        self.error_display.setWordWrap(True)
        self.error_display.setFixedWidth(300)
        self.error_display.setMinimumHeight(100)
        self.error_display.hide()

        # Обновление интерфейса
        self.refresh_ui()
        self.compute_params()

    def fetch_translations(self, lang):
        try:
            with open(get_resource_path("Texts.json"), "r", encoding="utf-8") as f:
                texts_data = json.load(f)
                return texts_data[lang]["translations"]
        except:
            return {
                "window_title": "FMCW Радар" if lang == "ru" else "FMCW Radar",
                "plot_xlabel": "Время, с" if lang == "ru" else "Time, s",
                "plot_ylabel": "Частота, ГГц" if lang == "ru" else "Frequency, GHz",
                "plot_title": "График ЛЧМ сигнала" if lang == "ru" else "FMCW Signal Plot",
                "limits_window_title": "Ограничения" if lang == "ru" else "Limits",
                "priorities_window_title": "Приоритеты" if lang == "ru" else "Priorities",
                "btn_limits": "Ограничения" if lang == "ru" else "Limits",
                "btn_save": "Сохранить" if lang == "ru" else "Save",
                "btn_open": "Открыть" if lang == "ru" else "Open",
                "btn_toggle_theme": "Сменить тему" if lang == "ru" else "Toggle Theme",
                "btn_change_language": "Сменить язык" if lang == "ru" else "Change Language",
                "btn_priorities": "Приоритеты" if lang == "ru" else "Priorities",
                "btn_help": "Справка" if lang == "ru" else "Help"
            }

    def update_param_history(self, param, text):
        if param not in EDITABLE_PARAMS:
            return
        si_value = convert_to_si(param, text)
        if text.strip() and text != "0" and si_value is not None:
            if param not in self.param_history:
                self.param_history.append(param)
        elif param in self.param_history:
            self.param_history.remove(param)

    def apply_theme(self, theme):
        try:
            with open(get_resource_path(f"{theme}_theme.qss"), "r", encoding="utf-8") as f:
                QtWidgets.QApplication.instance().setStyleSheet(f.read())
        except:
            pass

    def refresh_ui(self):
        self.setWindowTitle(self.translations.get("window_title", ""))
        for param, label in [(p, self.findChild(QtWidgets.QLabel, f"label_input_{p}")) for p in PARAMS]:
            if label:
                label.setText(self.translations.get(param, ""))
        for btn, key in [(self.btn_reset, "btn_clear_all"), (self.btn_compute, "btn_calculate"), (self.btn_menu, "btn_menu")]:
            if btn:
                btn.setText(self.translations.get(key, ""))
        if self.btn_menu:
            for act, key in [
                (self.act_save, "btn_save"), (self.act_load, "btn_open"),
                (self.act_theme, "btn_toggle_theme"), (self.act_lang, "btn_change_language"),
                (self.act_priorities, "btn_priorities"), (self.act_limits, "btn_limits"),
                (self.act_help, "btn_help")
            ]:
                act.setText(self.translations.get(key, "Ограничения" if key == "btn_limits" and self.lang == "ru" else "Limits" if key == "btn_limits" else ""))

    def handle_field_keypress(self, event, param):
        key = event.key()
        text = event.text().lower()
        field = self.fields[param]
        cursor = field.cursorPosition()

        actions = {
            (Qt.Key_S, 's'): self.save_params, (Qt.Key_S, 'ы'): self.save_params,
            (Qt.Key_O, 'o'): self.load_params, (Qt.Key_O, 'щ'): self.load_params,
            (Qt.Key_C, 'c'): self.reset_all, (Qt.Key_C, 'с'): self.reset_all,
            (Qt.Key_T, 't'): self.switch_theme, (Qt.Key_T, 'е'): self.switch_theme,
            (Qt.Key_L, 'l'): self.switch_language, (Qt.Key_L, 'д'): self.switch_language,
            (Qt.Key_P, 'p'): self.toggle_priorities, (Qt.Key_P, 'з'): self.toggle_priorities,
            (Qt.Key_D, 'd'): self.toggle_limits, (Qt.Key_D, 'в'): self.toggle_limits,
            (Qt.Key_H, 'h'): self.show_help, (Qt.Key_H, 'р'): self.show_help,
        }

        for (k, t), func in actions.items():
            if key == k or text == t:
                func()
                field.setFocus()
                field.setCursorPosition(cursor)
                return
        QtWidgets.QLineEdit.keyPressEvent(field, event)

    def show_error(self, msg):
        self.error_display.setText(msg)
        self.error_display.show()
        self.error_display.move(self.width() - 310, self.height() - 110)
        QTimer.singleShot(8000, self.error_display.hide)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.error_display.isVisible():
            self.error_display.move(self.width() - 310, self.height() - 110)

    def switch_language(self):
        self.lang = 'en' if self.lang == 'ru' else 'ru'
        self.settings.setValue("language", self.lang)
        self.translations = self.fetch_translations(self.lang)
        self.refresh_ui()
        self.compute_params()

    def switch_theme(self):
        self.dark_mode = not self.dark_mode
        self.settings.setValue("theme", "dark" if self.dark_mode else "light")
        self.apply_theme("dark" if self.dark_mode else "light")
        self.compute_params()

    def toggle_priorities(self):
        if self.priorities_dialog is not None and self.priorities_dialog.isVisible():
            self.priorities_dialog.close()
        else:
            self.priorities_dialog = PrioritiesDialog(self, self.translations, self.priorities)
            self.priorities_dialog.show()

    def toggle_limits(self):
        if self.limits_dialog and self.limits_dialog.isVisible():
            self.limits_dialog.close()
        else:
            self.limits_dialog = LimitsDialog(self, self.translations, self.limits, self.settings)
            self.limits_dialog.show()

    def show_help(self):
        dialog = HelpDialog(self, self.translations, self.lang)
        dialog.exec_()

    def keyPressEvent(self, event):
        key = event.key()
        text = event.text().lower()
        if key in (Qt.Key_Return, Qt.Key_Enter):
            self.compute_params()
        elif key == Qt.Key_S or text == 'ы':
            self.save_params()
        elif key == Qt.Key_O or text == 'щ':
            self.load_params()
        elif key == Qt.Key_C or text == 'с':
            self.reset_all()
        elif key == Qt.Key_T or text == 'е':
            self.switch_theme()
        elif key == Qt.Key_L or text == 'д':
            self.switch_language()
        elif key == Qt.Key_P or text == 'з':
            self.toggle_priorities()
        elif key == Qt.Key_D or text == 'в':
            self.toggle_limits()
        elif key == Qt.Key_H or text == 'р':
            self.show_help()
        elif key in (Qt.Key_Up, Qt.Key_Down):
            current = self.focusWidget()
            if current in self.fields.values():
                curr_param = current.objectName().replace("input_", "")
                curr_idx = FOCUS_ORDER.index(curr_param)
                if key == Qt.Key_Up:
                    next_idx = (curr_idx - 1) % len(FOCUS_ORDER)
                else:  # Qt.Key_Down
                    next_idx = (curr_idx + 1) % len(FOCUS_ORDER)
                self.fields[FOCUS_ORDER[next_idx]].setFocus()
            elif not current or current == self or isinstance(current, QtWidgets.QPushButton):
                self.fields[FOCUS_ORDER[0]].setFocus()
            return
        super().keyPressEvent(event)

    def clear_param(self, param):
        if param in self.fields:
            self.fields[param].setText("")
            self.fields[param].setStyleSheet("")
            if param in self.param_history:
                self.param_history.remove(param)

    def compute_params(self):
        # Собираем текущие параметры из полей ввода
        current_params = {}
        for param in PARAMS:
            text = self.fields[param].text().strip()
            if text and text != "0":
                si_value = convert_to_si(param, text)
                if si_value is not None:
                    current_params[param] = si_value

        # Определяем входные и выходные параметры
        input_params = {'dres', 'vres', 'dmax', 'vmax', 'f0'}
        output_params = {'lambda_', 'Tc', 'B', 'S', 'N', 'Tf', 'Fif', 'mem'}

        # Проверяем, есть ли среди введённых пользователем параметров хотя бы один выходной
        has_output_param = any(param in output_params for param in self.param_history)

        # Если нет ни одного выходного параметра в истории, удаляем выходные параметры из current_params
        if not has_output_param:
            for param in output_params:
                current_params.pop(param, None)

        try:
            # Вызываем функцию расчёта параметров
            results = calculate_parameters(current_params, self.param_history, self.priorities)
            param_order = ['f0', 'lambda_', 'Tc', 'B', 'S', 'N', 'Tf', 'Fif', 'vmax', 'dres', 'vres', 'dmax']
            updated_params = dict(zip(param_order, results))

            # Обновляем поля интерфейса с округлением до трёх значащих цифр
            for param, val in updated_params.items():
                if param in self.fields and param != 'mem':
                    if val is not None:
                        display_val = val
                        if param in ('f0', 'B'):
                            display_val /= 1e9  # ГГц
                        elif param == 'Tc':
                            display_val *= 1e3  # мс
                        elif param == 'S':
                            display_val /= 1e12  # ГГц/мкс
                        elif param == 'Fif':
                            display_val /= 1e6  # МГц
                        rounded_val = round_to_three_significant(display_val)
                        self.fields[param].setText(str(rounded_val) if rounded_val != 0 else "0")
                    else:
                        self.fields[param].setText("")

            # Обновляем current_params с результатами расчета
            for param in updated_params:
                if updated_params[param] is not None:
                    current_params[param] = updated_params[param]

            # Проверка ограничений и подсветка красным
            for param in PARAMS:
                if param == 'mem':
                    continue
                field = self.fields[param]
                display_val = field.text().strip()
                if not display_val or display_val == "0":
                    field.setStyleSheet("")
                    continue
                display_val = float(display_val)
                limit = self.limits.get(param)
                if limit is not None:
                    if param in ('f0', 'B'):
                        display_val *= 1e9  # ГГц → Гц
                        limit *= 1e9 if param == 'f0' else 1e6  # B в МГц
                    elif param == 'Tc':
                        display_val *= 1e-3  # мс → с
                    elif param == 'S':
                        display_val *= 1e12  # ГГц/мкс → Гц/с
                        limit *= 1e15  # ГГц/мкс → Гц/с
                    elif param == 'Fif':
                        display_val *= 1e6  # МГц → Гц
                        limit *= 1e6  # МГц → Гц
                    if display_val >= limit:
                        field.setStyleSheet("background-color: #FF4040;")
                    else:
                        field.setStyleSheet("")
                else:
                    field.setStyleSheet("")

            # Расчет памяти: mem = (N * (Fif * Tc)) в байтах, затем в Мб
            if 'Fif' in current_params and 'N' in current_params and 'Tc' in current_params:
                Fif = current_params['Fif']  # В Гц (convert_to_si уже преобразует из МГц)
                N = int(current_params['N'])  # Без преобразования, так как это целое число
                Tc = current_params['Tc']     # В секундах (convert_to_si преобразует из мс)
                sample_size = 2  # 16 бит = 2 байта на отсчет
                memory_bytes = N * (Fif * Tc) * sample_size  # Байты
                memory_mb = memory_bytes / (1024 * 1024)     # Мб
                rounded_memory = round_to_three_significant(memory_mb)
                self.fields['mem'].setText(f"{rounded_memory:.2f}" if rounded_memory > 0 else "0")
            else:
                self.fields['mem'].setText("0")

            # Построение графика
            if 'f0' in current_params and 'B' in current_params and 'Tc' in current_params and 'N' in current_params and 'Tf' in current_params:
                self.fig.clf()
                ax = self.fig.add_subplot(111)
                f0 = current_params['f0'] / 1e9  # ГГц
                B = current_params['B'] / 1e9    # ГГц
                Tc = current_params['Tc']        # с
                N = min(int(current_params['N']), 16)  # Ограничение до 16 чирпов
                Tf = current_params['Tf']        # с

                t_total = Tc * N  # Время для N чирпов
                t = [0]
                f = [f0]
                for i in range(N):
                    t_start = i * Tc
                    t.extend([t_start, t_start + Tc])
                    f.extend([f0, f0 + B])
                    t.append(t_start + Tc)
                    f.append(f0)
                t = t[:-1]  # Удаляем последний повторяющийся элемент
                f = f[:-1]

                ax.plot(t, f, 'b-')
                ax.set_xlim(0, t_total)
                ax.set_ylim(f0, f0 + B)
                ax.grid(True)
                style_plot(self.fig, self.dark_mode, self.translations)
                self.canvas.draw()
            else:
                draw_empty_plot(self.canvas, self.fig, self.dark_mode, self.translations)

        except Exception as e:
            self.show_error(f"Ошибка: {e}")
            draw_empty_plot(self.canvas, self.fig, self.dark_mode, self.translations)

    def reset_all(self):
        for field in self.fields.values():
            field.setText("")
            field.setStyleSheet("")
        self.param_history = []
        draw_empty_plot(self.canvas, self.fig, self.dark_mode, self.translations)

    def save_params(self):
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, self.translations['btn_save'], "", "Text Files (*.txt);;All Files (*)")
        if not fname:
            return
        if not fname.endswith('.txt'):
            fname += '.txt'
        with open(fname, 'w', encoding='utf-8') as f:
            for param in PARAMS:
                f.write(f"{param}={self.fields[param].text().strip()}\n")

    def load_params(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(self, self.translations['btn_open'], "", "Text Files (*.txt);;All Files (*)")
        if not fname or not fname.endswith('.txt'):
            return
        with open(fname, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        params = {}
        for line in lines:
            if '=' in line:
                key, val = line.strip().split('=', 1)
                if key in PARAMS:
                    params[key] = val
        if len(params) != len(PARAMS):
            self.show_error(self.translations['error_load_invalid'])
            return
        self.param_history = []
        for param in EDITABLE_PARAMS:
            self.fields[param].setText(params[param])
            if params[param].strip() and params[param] != "0":
                self.param_history.append(param)
        self.fields['mem'].setText(params['mem'])
        self.compute_params()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = RadarApp()
    window.show()
    sys.exit(app.exec_())