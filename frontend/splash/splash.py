# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'splashkfbeqF.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QLabel, QProgressBar, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_Splash(object):
    def setupUi(self, Splash):
        if not Splash.objectName():
            Splash.setObjectName(u"Splash")
        Splash.resize(642, 295)
        self.verticalLayout = QVBoxLayout(Splash)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.logo_label = QLabel(Splash)
        self.logo_label.setObjectName(u"logo_label")

        self.verticalLayout.addWidget(self.logo_label, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)

        self.app_name_label = QLabel(Splash)
        self.app_name_label.setObjectName(u"app_name_label")

        self.verticalLayout.addWidget(self.app_name_label, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)

        self.version_label = QLabel(Splash)
        self.version_label.setObjectName(u"version_label")

        self.verticalLayout.addWidget(self.version_label, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)

        self.progress_bar = QProgressBar(Splash)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setValue(24)

        self.verticalLayout.addWidget(self.progress_bar)

        self.status_label = QLabel(Splash)
        self.status_label.setObjectName(u"status_label")

        self.verticalLayout.addWidget(self.status_label)


        self.retranslateUi(Splash)

        QMetaObject.connectSlotsByName(Splash)
    # setupUi

    def retranslateUi(self, Splash):
        Splash.setWindowTitle(QCoreApplication.translate("Splash", u"Form", None))
        self.logo_label.setText("")
        self.app_name_label.setText("")
        self.version_label.setText("")
        self.status_label.setText(QCoreApplication.translate("Splash", u"Loading...", None))
    # retranslateUi

