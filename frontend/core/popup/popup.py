# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'popupbqMDro.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_Popup(object):
    def setupUi(self, Popup):
        if not Popup.objectName():
            Popup.setObjectName(u"Popup")
        Popup.resize(300, 300)
        Popup.setMinimumSize(QSize(300, 300))
        self.verticalLayout = QVBoxLayout(Popup)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.icon = QLabel(Popup)
        self.icon.setObjectName(u"icon")

        self.horizontalLayout.addWidget(self.icon, 0, Qt.AlignmentFlag.AlignHCenter)

        self.header = QLabel(Popup)
        self.header.setObjectName(u"header")

        self.horizontalLayout.addWidget(self.header, 0, Qt.AlignmentFlag.AlignLeft)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 10)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.message = QLabel(Popup)
        self.message.setObjectName(u"message")

        self.verticalLayout.addWidget(self.message, 0, Qt.AlignmentFlag.AlignHCenter)

        self.frame = QFrame(Popup)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.okbtn = QPushButton(self.frame)
        self.okbtn.setObjectName(u"okbtn")

        self.horizontalLayout_2.addWidget(self.okbtn)

        self.cancelbtn = QPushButton(self.frame)
        self.cancelbtn.setObjectName(u"cancelbtn")

        self.horizontalLayout_2.addWidget(self.cancelbtn)


        self.verticalLayout.addWidget(self.frame, 0, Qt.AlignmentFlag.AlignRight)

        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 3)

        self.retranslateUi(Popup)

        QMetaObject.connectSlotsByName(Popup)
    # setupUi

    def retranslateUi(self, Popup):
        Popup.setWindowTitle(QCoreApplication.translate("Popup", u"Form", None))
        self.icon.setText(QCoreApplication.translate("Popup", u"Icon", None))
        self.header.setText(QCoreApplication.translate("Popup", u"Header", None))
        self.message.setText(QCoreApplication.translate("Popup", u"Info", None))
        self.okbtn.setText(QCoreApplication.translate("Popup", u"Okay", None))
        self.cancelbtn.setText(QCoreApplication.translate("Popup", u"Cancel", None))
    # retranslateUi

