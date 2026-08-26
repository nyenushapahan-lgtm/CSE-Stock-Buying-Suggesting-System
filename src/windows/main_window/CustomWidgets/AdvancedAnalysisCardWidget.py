from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QLabel, QProgressBar, QWidget, QSizePolicy)
from PySide6.QtCore import Qt

class AdvancedAnalysisCardWidget(QFrame):
    def __init__(self, stock_code, stock_name, current_price, target_price, 
                 signal, confidence, rsi, macd, volume_trend, ai_summary):
        super().__init__()
        
        # Main Card Styling (Dark Theme, Rounded Corners)
        self.setStyleSheet("""
            AdvancedAnalysisCardWidget {
                background-color: #1A1A24;
                border-radius: 12px;
                border: 1px solid #2D2D3D;
            }
            QLabel { color: #E0E0E0; font-family: 'Segoe UI', Arial, sans-serif; }
        """)
        
        # Main Layout with inner padding
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # ==========================================
        # 1. HEADER: Stock Info & Signal Badge
        # ==========================================
        header_layout = QHBoxLayout()
        
        # Title and Subtitle
        title_layout = QVBoxLayout()
        lbl_code = QLabel(stock_code)
        lbl_code.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        lbl_name = QLabel(stock_name)
        lbl_name.setStyleSheet("font-size: 14px; color: #8A8A9E;")
        title_layout.addWidget(lbl_code)
        title_layout.addWidget(lbl_name)
        
        # Signal Badge (Buy = Green, Sell = Red, Hold = Yellow)
        lbl_signal = QLabel(signal.upper())
        lbl_signal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_signal.setFixedSize(100, 35)
        
        signal_color = "#4CAF50" if "BUY" in signal.upper() else "#F44336" if "SELL" in signal.upper() else "#FFC107"
        bg_color = f"{signal_color}33" # Adding '33' makes the background transparent/faded
        
        lbl_signal.setStyleSheet(f"""
            background-color: {bg_color};
            color: {signal_color};
            border: 1px solid {signal_color};
            border-radius: 6px;
            font-size: 14px;
            font-weight: bold;
        """)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(lbl_signal)
        main_layout.addLayout(header_layout)

        # ==========================================
        # 2. PRICE & CONFIDENCE SECTION
        # ==========================================
        price_conf_layout = QHBoxLayout()
        
        # Prices
        price_layout = QVBoxLayout()
        lbl_current = QLabel(f"Current Price: Rs. {current_price:.2f}")
        lbl_current.setStyleSheet("font-size: 16px;")
        lbl_target = QLabel(f"AI Target Price: Rs. {target_price:.2f}")
        lbl_target.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {signal_color};")
        price_layout.addWidget(lbl_current)
        price_layout.addWidget(lbl_target)
        
        # Confidence Meter
        conf_layout = QVBoxLayout()
        conf_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        lbl_conf_title = QLabel("AI Confidence Score")
        lbl_conf_title.setStyleSheet("font-size: 12px; color: #8A8A9E;")
        lbl_conf_title.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        progress_bar = QProgressBar()
        progress_bar.setFixedSize(150, 10)
        progress_bar.setValue(confidence)
        progress_bar.setTextVisible(False)
        progress_bar.setStyleSheet(f"""
            QProgressBar {{ border: none; background-color: #2D2D3D; border-radius: 5px; }}
            QProgressBar::chunk {{ background-color: {signal_color}; border-radius: 5px; }}
        """)
        
        lbl_conf_val = QLabel(f"{confidence}%")
        lbl_conf_val.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        lbl_conf_val.setAlignment(Qt.AlignmentFlag.AlignRight)

        conf_layout.addWidget(lbl_conf_title)
        conf_layout.addWidget(progress_bar)
        conf_layout.addWidget(lbl_conf_val)

        price_conf_layout.addLayout(price_layout)
        price_conf_layout.addStretch()
        price_conf_layout.addLayout(conf_layout)
        main_layout.addLayout(price_conf_layout)

        # Divider Line
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #2D2D3D;")
        main_layout.addWidget(divider)

        # ==========================================
        # 3. TECHNICAL INDICATORS (Grid Layout)
        # ==========================================
        lbl_tech_title = QLabel("Technical Analysis")
        lbl_tech_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #8A8A9E;")
        main_layout.addWidget(lbl_tech_title)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        # Helper function to create small stat boxes
        def create_stat_box(title, value, is_positive=None):
            box = QFrame()
            box.setStyleSheet("background-color: #222230; border-radius: 8px; padding: 10px;")
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(10, 10, 10, 10)
            
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("font-size: 12px; color: #8A8A9E; border: none;")
            
            v_lbl = QLabel(value)
            val_color = "#FFFFFF"
            if is_positive is True: val_color = "#4CAF50"
            elif is_positive is False: val_color = "#F44336"
            
            v_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {val_color}; border: none;")
            
            box_layout.addWidget(t_lbl)
            box_layout.addWidget(v_lbl)
            return box

        # Determine colors based on text logic (You can adjust this logic based on your actual data)
        rsi_pos = True if "Oversold" in rsi or float(rsi.split()[0]) < 40 else False if float(rsi.split()[0]) > 70 else None
        macd_pos = True if "Bullish" in macd else False if "Bearish" in macd else None
        
        grid_layout.addWidget(create_stat_box("RSI (14 Days)", rsi, rsi_pos), 0, 0)
        grid_layout.addWidget(create_stat_box("MACD", macd, macd_pos), 0, 1)
        grid_layout.addWidget(create_stat_box("Volume Trend", volume_trend, True if "High" in volume_trend else None), 0, 2)
        
        main_layout.addLayout(grid_layout)

        # ==========================================
        # 4. DEEP SEEK AI SUMMARY
        # ==========================================
        lbl_summary_title = QLabel("Deep Seek News & Sentiment Analysis")
        lbl_summary_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #8A8A9E; margin-top: 10px;")
        main_layout.addWidget(lbl_summary_title)

        lbl_summary = QLabel(ai_summary)
        lbl_summary.setWordWrap(True)
        lbl_summary.setStyleSheet("""
            font-size: 13px; 
            color: #CCCCCC; 
            line-height: 1.5; 
            background-color: #222230; 
            padding: 15px; 
            border-radius: 8px;
            border-left: 3px solid #2D63E2;
        """)
        main_layout.addWidget(lbl_summary)

        # Push everything to the top so it doesn't stretch weirdly if the window is tall
        main_layout.addStretch()