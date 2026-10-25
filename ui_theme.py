"""Soft daylight theme for the desktop app."""
STYLE = '''
QWidget { color:#29483f; font:13px "Microsoft YaHei UI"; }
QMainWindow, QWidget#shell, QWidget#page { background:#f7f8f2; }
QFrame#sidebar { background:#edf3e9; border-right:1px solid #dce5d9; }
QFrame#card { background:#ffffff; border:1px solid #dfe7dc; border-radius:16px; }
QFrame#hero { background:#eaf3e4; border:1px solid #d4e5ce; border-radius:16px; }
QFrame#footer { background:#ffffff; border-top:1px solid #e3e9df; }
QLabel { background:transparent; }
QLabel#brand { font-size:29px; font-weight:800; color:#335a49; letter-spacing:3px; }
QLabel#heading { font-size:25px; font-weight:700; color:#274c3d; }
QLabel#cardTitle { font-size:16px; font-weight:600; }
QLabel#muted { color:#65766b; font-size:12px; }
QLabel#eyebrow { color:#65866a; font-size:10px; letter-spacing:2px; font-weight:600; }
QLabel#badge { background:#e5f1df; color:#3d6846; border:1px solid #d1e3c7; border-radius:12px; padding:6px 12px; font-size:12px; }
QLabel#metric { color:#6c7e71; font-size:11px; }
QLabel#preview { background:#f1f4ec; border:1px dashed #c8d7c2; border-radius:12px; color:#718369; }
QLabel#task { background:#eff5e9; border:1px solid #d7e4d0; border-radius:10px; padding:12px; color:#355b40; }
QPushButton { background:#ffffff; border:1px solid #ccd9c7; border-radius:10px; padding:9px 14px; color:#49614c; }
QPushButton:hover { background:#f0f6e9; border-color:#a5bea0; }
QPushButton:pressed { background:#dbe9d1; }
QPushButton:disabled { color:#99a291; background:#f1f3ed; border-color:#e1e7dc; }
QPushButton#primary { background:#547a50; border:1px solid #547a50; color:#ffffff; font-weight:700; }
QPushButton#primary:hover { background:#42683e; }
QPushButton#primary:disabled { background:#c6d6bf; color:#eff4eb; border-color:#c6d6bf; }
QPushButton#record { background:#fbebe3; border-color:#e8c8b5; color:#a65b3c; font-weight:700; }
QPushButton#record:checked { background:#bd6e52; color:white; }
QPushButton#nav { text-align:left; background:transparent; border:0; border-radius:12px; padding:13px 14px; color:#63775d; }
QPushButton#nav:hover { background:#e2edd9; }
QPushButton#nav:checked { background:#d8e7cd; color:#335a34; font-weight:700; }
QPushButton#disclosure { text-align:left; background:transparent; border:0; color:#6a7e63; padding:7px 0; }
QLineEdit, QTextEdit, QComboBox { background:#fafbf7; color:#29483f; border:1px solid #d9e2d3; border-radius:9px; padding:8px; selection-background-color:#d2e5c7; selection-color:#29483f; }
QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border-color:#80a775; }
QComboBox::drop-down { border:0; width:22px; }
QComboBox QAbstractItemView { background:#ffffff; color:#29483f; selection-background-color:#dceccd; selection-color:#29483f; }
QTextEdit#transcript { font-size:17px; }
QListWidget { background:transparent; border:0; color:#637761; font-size:12px; outline:0; }
QListWidget::item { padding:8px 0; border-bottom:1px solid #e8ede3; }
QTableWidget { background:#ffffff; border:1px solid #dbe5d3; border-radius:9px; gridline-color:#edf1e8; selection-background-color:#e4efd9; selection-color:#29483f; }
QHeaderView::section { background:#eef4e7; color:#64785a; border:0; padding:9px; }
QTableWidget::item { padding:6px; }
QProgressBar { border:0; border-radius:4px; background:#e3ebdc; height:8px; text-align:center; }
QProgressBar::chunk { background:#8caa73; border-radius:4px; }
QScrollArea { border:0; background:transparent; }
QScrollBar:vertical { width:7px; background:#f1f4ec; }
QScrollBar::handle:vertical { background:#c2d2b6; border-radius:3px; min-height:30px; }
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0; }
'''
