# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'testerBbRIkg.ui'
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
from PySide6.QtWidgets import (QApplication, QMainWindow, QMenu, QMenuBar,
    QSizePolicy, QStatusBar, QWidget)

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
        TesterWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(TesterWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 33))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        TesterWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(TesterWindow)
        self.statusbar.setObjectName(u"statusbar")
        TesterWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionClose)
        self.menuFile.addAction(self.actionAbout)

        self.retranslateUi(TesterWindow)

        QMetaObject.connectSlotsByName(TesterWindow)
    # setupUi

    def retranslateUi(self, TesterWindow):
        TesterWindow.setWindowTitle(QCoreApplication.translate("TesterWindow", u"MainWindow", None))
        self.actionClose.setText(QCoreApplication.translate("TesterWindow", u"Close", None))
        self.actionAbout.setText(QCoreApplication.translate("TesterWindow", u"About", None))
        self.menuFile.setTitle(QCoreApplication.translate("TesterWindow", u"File", None))
    # retranslateUi

