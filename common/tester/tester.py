# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'testerrNQxPV.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QSizePolicy,
    QStatusBar, QTabWidget, QVBoxLayout, QWidget)

class Ui_TesterWindow(object):
    def setupUi(self, TesterWindow):
        if not TesterWindow.objectName():
            TesterWindow.setObjectName(u"TesterWindow")
        TesterWindow.resize(800, 600)
        self.actionClose = QAction(TesterWindow)
        self.actionClose.setObjectName(u"actionClose")
        self.actionAbout = QAction(TesterWindow)
        self.actionAbout.setObjectName(u"actionAbout")
        self.centralwidget = QWidget(TesterWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.titlebar = QWidget(self.centralwidget)
        self.titlebar.setObjectName(u"titlebar")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.titlebar.sizePolicy().hasHeightForWidth())
        self.titlebar.setSizePolicy(sizePolicy)
        self.titlebar.setMinimumSize(QSize(0, 40))
        self.horizontalLayout_2 = QHBoxLayout(self.titlebar)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")

        self.verticalLayout.addWidget(self.titlebar)

        self.main_tw = QTabWidget(self.centralwidget)
        self.main_tw.setObjectName(u"main_tw")

        self.verticalLayout.addWidget(self.main_tw)

        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 20)
        TesterWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(TesterWindow)
        self.statusbar.setObjectName(u"statusbar")
        TesterWindow.setStatusBar(self.statusbar)

        self.retranslateUi(TesterWindow)

        QMetaObject.connectSlotsByName(TesterWindow)
    # setupUi

    def retranslateUi(self, TesterWindow):
        TesterWindow.setWindowTitle(QCoreApplication.translate("TesterWindow", u"MainWindow", None))
        self.actionClose.setText(QCoreApplication.translate("TesterWindow", u"Close", None))
        self.actionAbout.setText(QCoreApplication.translate("TesterWindow", u"About", None))
    # retranslateUi

