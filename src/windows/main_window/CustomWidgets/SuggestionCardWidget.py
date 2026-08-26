import sys
from PySide6.QtWidgets import QWidget,QApplication, QMainWindow, QTableWidgetItem, QMessageBox,QButtonGroup,QFrame,QVBoxLayout,QHBoxLayout,QLabel,QProgressBar,QPushButton,QHeaderView
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile,Qt,QMargins,QDateTime
from src.services import handleThems
from PySide6.QtGui import QIcon, QPixmap,QPainter,QBrush,QColor

class SuggestionCardWidget(QFrame):
    """Custom UI Card for detailed AI Stock Analysis"""
    def __init__(self, stock_name, current_price, target_price, verdict, confidence, rsi, macd, news):
        super().__init__()
        
        # Style the main card (Dark modern theme)
        self.setStyleSheet("""
            SuggestionCardWidget {
                background-color: #1E1E2E;
                border-radius: 10px;
                border: 1px solid #333344;
            }
            QLabel { color: white; }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(25, 25, 25, 25)

        # --- 1. Header (Stock Name) ---
        lbl_title = QLabel(stock_name)
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #E0E0E0;")
        main_layout.addWidget(lbl_title)

        # --- 2. Prices ---
        price_layout = QHBoxLayout()
        lbl_current = QLabel(f"Current: Rs. {current_price:.2f}")
        lbl_current.setStyleSheet("font-size: 14px; color: #AAAAAA;")
        lbl_target = QLabel(f"Target: Rs. {target_price:.2f}")
        lbl_target.setStyleSheet("font-size: 14px; color: #4CAF50; font-weight: bold;")
        price_layout.addWidget(lbl_current)
        price_layout.addWidget(lbl_target)
        price_layout.addStretch()
        main_layout.addLayout(price_layout)

        # --- 3. AI Verdict ---
        lbl_verdict = QLabel(verdict)
        verdict_color = "#4CAF50" if "BUY" in verdict.upper() else "#F44336" if "SELL" in verdict.upper() else "#FFC107"
        lbl_verdict.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {verdict_color}; margin-top: 10px;")
        lbl_verdict.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(lbl_verdict)

        # --- 4. Confidence Meter ---
        conf_layout = QHBoxLayout()
        lbl_conf_text = QLabel("AI Confidence:")
        lbl_conf_text.setStyleSheet("font-size: 12px; color: #888888;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(confidence)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat(f"{confidence}%")
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none; background-color: #2A2A3C; border-radius: 7px; color: white; text-align: center; font-size: 10px;
            }}
            QProgressBar::chunk {{
                background-color: {verdict_color}; border-radius: 7px;
            }}
        """)
        conf_layout.addWidget(lbl_conf_text)
        conf_layout.addWidget(self.progress_bar)
        main_layout.addLayout(conf_layout)

        # --- 5. Technical Factors ---
        lbl_factors = QLabel("Key Technical Factors:")
        lbl_factors.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(lbl_factors)

        lbl_rsi = QLabel(f"• RSI: {rsi}")
        lbl_macd = QLabel(f"• MACD: {macd}")
        main_layout.addWidget(lbl_rsi)
        main_layout.addWidget(lbl_macd)

        # --- 6. AI News Sentiment ---
        lbl_news_title = QLabel("AI News Sentiment:")
        lbl_news_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(lbl_news_title)

        lbl_news = QLabel(news)
        lbl_news.setWordWrap(True)
        lbl_news.setStyleSheet("font-size: 12px; color: #CCCCCC; font-style: italic;")
        main_layout.addWidget(lbl_news)
