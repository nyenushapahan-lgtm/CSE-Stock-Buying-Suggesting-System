from PySide6.QtWidgets import (QWidget, QApplication, QMainWindow, QTableWidgetItem, 
                               QMessageBox, QButtonGroup, QFrame, QVBoxLayout, QHBoxLayout, 
                               QLabel, QProgressBar, QPushButton, QHeaderView, QTableWidget)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QMargins, QDateTime
from PySide6.QtGui import QIcon, QPainter, QBrush, QColor

from PySide6.QtCharts import (QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, 
                              QValueAxis, QLineSeries, QDateTimeAxis)

# ==========================================
# 1. SUGGESTION CARD WIDGET
# ==========================================
class SuggestionCardWidget(QFrame):
    """Custom UI Card for detailed AI Stock Analysis (Table View Click)"""
    def __init__(self, stock_name, current_price, target_price, verdict, confidence, rsi, macd, news):
        super().__init__()
        
        self.setStyleSheet("""
            SuggestionCardWidget { background-color: #1E1E2E;padding:15px; border: 1px solid #333344; }
            QLabel { color: white; }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(25, 25, 25, 25)

        lbl_title = QLabel(stock_name)
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #E0E0E0;")
        main_layout.addWidget(lbl_title)

        price_layout = QHBoxLayout()
        lbl_current = QLabel(f"Current: Rs. {current_price:.2f}")
        lbl_current.setStyleSheet("font-size: 14px; color: #AAAAAA;")
        lbl_target = QLabel(f"Target: Rs. {target_price:.2f}")
        lbl_target.setStyleSheet("font-size: 14px; color: #4CAF50; font-weight: bold;")
        price_layout.addWidget(lbl_current)
        price_layout.addWidget(lbl_target)
        price_layout.addStretch()
        main_layout.addLayout(price_layout)

        lbl_verdict = QLabel(verdict)
        verdict_color = "#4CAF50" if "BUY" in verdict.upper() else "#F44336" if "SELL" in verdict.upper() else "#FFC107"
        lbl_verdict.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {verdict_color}; margin-top: 10px;")
        lbl_verdict.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(lbl_verdict)

        conf_layout = QHBoxLayout()
        lbl_conf_text = QLabel("AI Confidence:")
        lbl_conf_text.setStyleSheet("font-size: 12px; color: #888888;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(confidence)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat(f"{confidence}%")
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{ border: none; background-color: #2A2A3C; border-radius: 7px; color: white; text-align: center; font-size: 10px; }}
            QProgressBar::chunk {{ background-color: {verdict_color}; border-radius: 7px; }}
        """)
        conf_layout.addWidget(lbl_conf_text)
        conf_layout.addWidget(self.progress_bar)
        main_layout.addLayout(conf_layout)

        lbl_factors = QLabel("Key Technical Factors:")
        lbl_factors.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(lbl_factors)

        main_layout.addWidget(QLabel(f"• RSI: {rsi}"))
        main_layout.addWidget(QLabel(f"• MACD: {macd}"))

        lbl_news_title = QLabel("AI News Sentiment:")
        lbl_news_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(lbl_news_title)

        lbl_news = QLabel(news)
        lbl_news.setWordWrap(True)
        lbl_news.setStyleSheet("font-size: 12px; color: #CCCCCC; font-style: italic;")
        main_layout.addWidget(lbl_news)


# ==========================================
# 2. ADVANCED ANALYSIS CARD WIDGET
# ==========================================
class AdvancedAnalysisCardWidget(QFrame):
    """Custom UI Card for Deep AI Insights (Main Dashboard)"""
    def __init__(self, stock_code, stock_name, current_price, target_price, signal, confidence, rsi, macd, volume_trend, ai_summary):
        super().__init__()
        
        self.setStyleSheet("""
            AdvancedAnalysisCardWidget { background-color: #1A1A24; border-radius: 12px; border: 1px solid #2D2D3D; }
            QLabel { color: #E0E0E0; font-family: 'Segoe UI', Arial, sans-serif; }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        lbl_code = QLabel(stock_code)
        lbl_code.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        lbl_name = QLabel(stock_name)
        lbl_name.setStyleSheet("font-size: 14px; color: #8A8A9E;")
        title_layout.addWidget(lbl_code)
        title_layout.addWidget(lbl_name)
        
        lbl_signal = QLabel(signal.upper())
        lbl_signal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_signal.setFixedSize(100, 35)
        signal_color = "#4CAF50" if "BUY" in signal.upper() else "#F44336" if "SELL" in signal.upper() else "#FFC107"
        lbl_signal.setStyleSheet(f"background-color: {signal_color}33; color: {signal_color}; border: 1px solid {signal_color}; border-radius: 6px; font-size: 14px; font-weight: bold;")

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(lbl_signal)
        main_layout.addLayout(header_layout)

        # Prices & Confidence
        price_conf_layout = QHBoxLayout()
        price_layout = QVBoxLayout()
        lbl_current = QLabel(f"Current: Rs. {current_price:.2f}")
        lbl_target = QLabel(f"Target: Rs. {target_price:.2f}")
        lbl_target.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {signal_color};")
        price_layout.addWidget(lbl_current)
        price_layout.addWidget(lbl_target)
        
        conf_layout = QVBoxLayout()
        lbl_conf_title = QLabel("AI Confidence Score")
        lbl_conf_title.setStyleSheet("font-size: 12px; color: #8A8A9E;")
        progress_bar = QProgressBar()
        progress_bar.setFixedSize(150, 10)
        progress_bar.setValue(confidence)
        progress_bar.setTextVisible(False)
        progress_bar.setStyleSheet(f"QProgressBar {{ border: none; background-color: #2D2D3D; border-radius: 5px; }} QProgressBar::chunk {{ background-color: {signal_color}; border-radius: 5px; }}")
        
        conf_layout.addWidget(lbl_conf_title, alignment=Qt.AlignmentFlag.AlignRight)
        conf_layout.addWidget(progress_bar, alignment=Qt.AlignmentFlag.AlignRight)

        price_conf_layout.addLayout(price_layout)
        price_conf_layout.addStretch()
        price_conf_layout.addLayout(conf_layout)
        main_layout.addLayout(price_conf_layout)

        # AI Summary
        lbl_summary_title = QLabel("Deep Seek Sentiment Analysis")
        lbl_summary_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #8A8A9E; margin-top: 10px;")
        main_layout.addWidget(lbl_summary_title)

        lbl_summary = QLabel(ai_summary)
        lbl_summary.setWordWrap(True)
        lbl_summary.setStyleSheet("font-size: 13px; color: #CCCCCC; background-color: #222230; padding: 15px; border-radius: 8px; border-left: 3px solid #2D63E2;")
        main_layout.addWidget(lbl_summary)
        main_layout.addStretch()
