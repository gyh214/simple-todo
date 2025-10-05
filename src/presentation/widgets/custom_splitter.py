# -*- coding: utf-8 -*-
"""
커스텀 Splitter 위젯

CustomSplitterHandle을 사용하는 QSplitter
"""
from PyQt6.QtWidgets import QSplitter
from PyQt6.QtCore import Qt

from src.presentation.widgets.custom_splitter_handle import CustomSplitterHandle


class CustomSplitter(QSplitter):
    """
    커스텀 Splitter

    createHandle() 오버라이드하여 CustomSplitterHandle 반환
    """

    def createHandle(self):
        """커스텀 핸들 생성"""
        return CustomSplitterHandle(self.orientation(), self)
