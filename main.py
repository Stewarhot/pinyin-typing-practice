import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


SHENGMU_ITEMS = [("b", "播"), ("p", "坡"), ("m", "摸"), ("f", "佛"), ("d", "得"), ("t", "特"), ("n", "呢"), ("l", "了"), ("g", "哥"), ("k", "科"), ("h", "喝"), ("j", "鸡"), ("q", "七"), ("x", "西"), ("zh", "知"), ("ch", "吃"), ("sh", "师"), ("r", "日"), ("z", "资"), ("c", "雌"), ("s", "思"), ("y", "衣"), ("w", "屋")]
YUNMU_ITEMS = [("a", "啊"), ("o", "喔"), ("e", "鹅"), ("i", "衣"), ("u", "乌"), ("ü", "迂"), ("ai", "爱"), ("ei", "诶"), ("ui", "威"), ("ao", "奥"), ("ou", "欧"), ("iu", "优"), ("ie", "约"), ("üe", "约"), ("er", "儿"), ("an", "安"), ("en", "恩"), ("in", "因"), ("un", "温"), ("ün", "晕"), ("ang", "昂"), ("eng", "鞥"), ("ing", "英"), ("ong", "翁")]
ZHENGTI_ITEMS = [("zhi", "知"), ("chi", "吃"), ("shi", "师"), ("ri", "日"), ("zi", "资"), ("ci", "雌"), ("si", "思"), ("yi", "衣"), ("wu", "乌"), ("yu", "鱼"), ("ye", "爷"), ("yue", "月"), ("yuan", "圆"), ("yin", "音"), ("yun", "云"), ("ying", "英")]


class PinyinTypingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("老年人拼音打字练习")
        self.resize(1100, 700)
        self.base_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
        self.data_dir = self.base_dir / "data"
        self.course_items = []
        self.current_index = 0
        self.correct_count = 0
        self.current_answer = ""
        self.current_type = ""
        self.changing_question = False
        self.formatting_text = False
        self.init_ui()
        self.show_reference("shengmu")

    def init_ui(self):
        self.setMinimumSize(900, 600)
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        left = QVBoxLayout()
        title = QLabel("课程内容")
        title.setFont(QFont("Microsoft YaHei", 18))
        title.setAlignment(Qt.AlignCenter)
        left.addWidget(title)
        courses = [
            ("1  声母练习", "shengmu.json"), ("2  韵母练习", "yunmu.json"),
            ("3  整体认读", "zhengti.json"), ("4  基础打字", "jichu.json"),
            ("5  拼音练习", "pinyin.json"), ("6  词组练习", "ciyu.json"),
            ("7  自定义短文1", "duanluo1.json"), ("8  自定义短文2", "duanluo2.json"),
            ("9  自定义短文3", "duanluo3.json"),
        ]
        for text, filename in courses:
            button = QPushButton(text)
            button.setMinimumHeight(40)
            button.clicked.connect(lambda checked=False, f=filename: self.load_course(f))
            left.addWidget(button)
        custom = QPushButton("10 选择JSON短文")
        custom.setMinimumHeight(40)
        custom.setToolTip("选择电脑上的 JSON 练习文件")
        custom.clicked.connect(self.choose_json_course)
        left.addWidget(custom)
        left.addStretch()
        layout.addLayout(left, 1)

        middle = QVBoxLayout()
        self.course_label = QLabel("练习内容：请选择课程")
        self.course_label.setAlignment(Qt.AlignCenter)
        self.course_label.setFont(QFont("Microsoft YaHei", 15))
        middle.addWidget(self.course_label)
        self.reference_text = QLabel("请选择左侧的练习项目")
        self.reference_text.setAlignment(Qt.AlignCenter)
        self.reference_text.setWordWrap(True)
        self.reference_text.setMinimumHeight(170)
        self.reference_text.setFont(QFont("Microsoft YaHei", 28))
        middle.addWidget(self.reference_text)
        self.input_prompt = QLabel("请输入答案")
        self.input_prompt.setAlignment(Qt.AlignCenter)
        middle.addWidget(self.input_prompt)
        self.input_edit = QTextEdit()
        self.input_edit.setFont(QFont("Microsoft YaHei", 26))
        self.input_edit.setMinimumHeight(180)
        self.input_edit.textChanged.connect(self.check_input)
        middle.addWidget(self.input_edit)
        self.tip = QLabel("请选择一个练习")
        self.tip.setAlignment(Qt.AlignCenter)
        middle.addWidget(self.tip)
        self.statistics = QLabel("本次练习：0/0题    正确：0题    正确率：0%")
        self.statistics.setAlignment(Qt.AlignCenter)
        middle.addWidget(self.statistics)
        layout.addLayout(middle, 3)

        right = QVBoxLayout()
        ref_title = QLabel("拼音参考")
        ref_title.setFont(QFont("Microsoft YaHei", 18))
        ref_title.setAlignment(Qt.AlignCenter)
        right.addWidget(ref_title)
        type_row = QHBoxLayout()
        for text, kind in (("声母", "shengmu"), ("韵母", "yunmu"), ("整体认读", "zhengti")):
            button = QPushButton(text)
            button.clicked.connect(lambda checked=False, k=kind: self.show_reference(k))
            type_row.addWidget(button)
        right.addLayout(type_row)
        box = QGroupBox()
        grid = QGridLayout(box)
        self.reference_buttons = []
        for i in range(24):
            button = QPushButton()
            button.setMinimumHeight(36)
            button.setEnabled(False)
            self.reference_buttons.append(button)
            grid.addWidget(button, i // 3, i % 3)
        right.addWidget(box)
        about = QPushButton("关于本软件")
        about.clicked.connect(self.show_about)
        right.addWidget(about)
        right.addStretch()
        layout.addLayout(right, 1)

    def choose_json_course(self):
        filename, _ = QFileDialog.getOpenFileName(self, "选择JSON练习文件", str(self.data_dir), "JSON 文件 (*.json)")
        if filename:
            self.load_course(Path(filename), Path(filename).stem)

    def load_course(self, filename, display_name=None):
        path = Path(filename)
        if not path.is_absolute():
            path = self.data_dir / path
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            items = data.get("items", []) if isinstance(data, dict) else data
            if not isinstance(items, list) or not items:
                raise ValueError("JSON 中的 items 必须是非空数组。")
        except Exception as error:
            QMessageBox.critical(self, "课程读取失败", f"JSON 文件读取失败：\n\n{path}\n\n{error}")
            return
        self.course_items = items
        self.current_index = 0
        self.correct_count = 0
        self.course_label.setText("练习内容：" + (display_name or path.stem))
        self.show_question()

    def show_reference(self, kind):
        items = {"shengmu": SHENGMU_ITEMS, "yunmu": YUNMU_ITEMS, "zhengti": ZHENGTI_ITEMS}.get(kind, SHENGMU_ITEMS)
        for button in self.reference_buttons:
            button.setText("")
            button.setEnabled(False)
        for button, (pinyin, pronunciation) in zip(self.reference_buttons, items):
            button.setText(f"{pinyin}  {pronunciation}")
            button.setEnabled(True)

    def show_question(self):
        if self.current_index >= len(self.course_items):
            return
        item = self.course_items[self.current_index]
        self.current_type = str(item.get("type", "")).lower() if isinstance(item, dict) else ""
        display = item.get("display", {}) if isinstance(item, dict) else {}
        if isinstance(display, dict):
            lines = display.get("lines", [])
            text = "\n".join(str(line.get("text", "")) if isinstance(line, dict) else str(line) for line in lines)
        else:
            text = str(display)
        self.reference_text.setText(text)
        answer = item.get("answer", "") if isinstance(item, dict) else ""
        self.current_answer = str(answer.get("text", "")) if isinstance(answer, dict) else str(answer)
        self.changing_question = True
        self.input_edit.clear()
        self.changing_question = False
        if self.current_type in {"sentence", "paragraph", "article", "word", "phrase", "ciyu"}:
            self.input_prompt.setText("我的输入：请直接输入上面的汉字（逐字判断）")
        else:
            self.input_prompt.setText("我的输入：请输入答案（逐字判断）")
        self.tip.setText("请输入答案")
        self.update_statistics()
        self.input_edit.setFocus()

    @staticmethod
    def normalize_text(text):
        return str(text).strip().lower().replace(" ", "").replace("　", "")

    def check_input(self):
        if self.changing_question or self.formatting_text or not self.course_items:
            return
        user = self.input_edit.toPlainText()
        answer = self.normalize_text(self.current_answer)
        self.color_input(user, answer)
        if self.normalize_text(user) == answer:
            self.handle_correct()

    def color_input(self, raw, answer):
        self.formatting_text = True
        try:
            cursor_position = self.input_edit.textCursor().position()
            document = self.input_edit.document()
            cursor = QTextCursor(document)
            cursor.select(QTextCursor.Document)
            base = QTextCharFormat()
            base.setForeground(QColor("#222222"))
            cursor.setCharFormat(base)
            normalized = [(i, ch.lower()) for i, ch in enumerate(raw) if ch not in " \u3000"]
            for n, (raw_index, char) in enumerate(normalized):
                color = "#008000" if n < len(answer) and char == answer[n] else "#D60000"
                char_cursor = QTextCursor(document)
                char_cursor.setPosition(raw_index)
                char_cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
                fmt = QTextCharFormat()
                fmt.setForeground(QColor(color))
                char_cursor.setCharFormat(fmt)
            new_cursor = self.input_edit.textCursor()
            new_cursor.setPosition(min(cursor_position, len(raw)))
            self.input_edit.setTextCursor(new_cursor)
            if not raw:
                self.tip.setText("请输入答案")
                self.tip.setStyleSheet("color:#666666")
            elif any(n >= len(answer) or ch != answer[n] for n, (_, ch) in enumerate(normalized)):
                self.tip.setText("红色文字有错误，请修改")
                self.tip.setStyleSheet("color:#D60000")
            else:
                self.tip.setText("目前输入正确，请继续")
                self.tip.setStyleSheet("color:#008000")
        finally:
            self.formatting_text = False

    def handle_correct(self):
        self.correct_count += 1
        self.update_statistics()
        self.tip.setText("✓ 回答正确！")
        self.tip.setStyleSheet("color:#008000; font-weight:bold")
        self.current_index += 1
        if self.current_index >= len(self.course_items):
            QTimer.singleShot(800, self.finish_course)
        else:
            QTimer.singleShot(800, self.show_question)

    def finish_course(self):
        self.reference_text.setText("🎉 恭喜！\n\n本次练习全部完成！")
        self.tip.setText("太棒了！请选择下一项练习。")
        self.update_statistics()
        QMessageBox.information(self, "练习完成", "恭喜您！\n\n本次练习已经全部完成。")

    def update_statistics(self):
        total = len(self.course_items)
        accuracy = self.correct_count / total * 100 if total else 0
        self.statistics.setText(f"本次练习：{self.correct_count}/{total}题    正确：{self.correct_count}题    正确率：{accuracy:.0f}%")

    def show_about(self):
        QMessageBox.information(self, "关于本软件", "老年人拼音打字练习\n\n用于拼音、汉字、词组和短文练习。\n\n学习拼音不怕慢，只要每天练习一点点，就会越来越熟练。\n年龄不是学习的障碍，坚持就是最好的进步。祝您学习愉快、打字越来越快！")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 12))
    window = PinyinTypingWindow()
    window.show()
    sys.exit(app.exec())
