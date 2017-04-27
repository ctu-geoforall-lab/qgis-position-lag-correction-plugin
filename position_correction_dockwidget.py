# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PositionCorrectionDockWidget
                                 A QGIS plugin
 Defines the interactions between widgets in GUI.

                             -------------------
        begin                : 2016-02-12
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Ondřej Pešek
        email                : pesej.ondrek@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal, QThread
from qgis.gui import QgsGenericProjectionSelector, QgsMessageBar
from qgis.core import QgsCoordinateReferenceSystem

from move import Move
import show_as_layer

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'position_correction_dockwidget_base.ui'))


class PositionCorrectionDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, parent=None):
        """Constructor"""

        super(PositionCorrectionDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.stylePath = None

        self.iface = iface
        self.computationRunning = False

        self.inputButton.clicked.connect(self.select_input)
        self.outputButton.clicked.connect(self.select_output)
        self.style.clicked.connect(self.select_style)
        self.showInput.clicked.connect(self.show_input)
        self.ellipsoidSelector.clicked.connect(self.select_ellipsoid)

        self.input.textChanged.connect(self.able_solve)  # enable solve button
        self.output.textChanged.connect(self.able_solve)
        self.value.textChanged.connect(self.able_solve)
        self.input.textChanged.connect(self.able_show)  # enable showInput btn

        self.solve.clicked.connect(self.solve_clicked)

    def select_input(self):
        """select csv file to edit"""

        self.filePath = QtGui.QFileDialog.getOpenFileName(
            self, 'Load file', '.', 'Comma Seperated Values (*.csv)')

        if self.filePath:
            self.filePath = os.path.normpath(self.filePath)
        else:
            return

        self.input.setText(self.filePath)
        self.output.setText(self.filePath[:-4]+u'_shifted.csv')

    def select_style(self):
        """select qml style file"""

        self.stylePath = QtGui.QFileDialog.getOpenFileName(
            self, 'Load file (Cancel causes "No style")',
            os.path.join(os.path.dirname(__file__), 'styles'),
            'Qt Meta Language (*.qml)')

        if self.stylePath:
            self.stylePath = os.path.normpath(self.stylePath)
            styleName = self.stylePath.split(os.path.sep)
            styleName = styleName[len(styleName)-1][:-4]
            self.style.setText(styleName)
        else:
            self.stylePath = None
            self.style.setText('No style')

    def select_output(self):
        """choose directory to save returned data"""

        self.outputDir = QtGui.QFileDialog.getExistingDirectory(self,
                                                          'Save to file')
        if not self.outputDir:
            return

        self.directory = os.path.normpath(self.outputDir) + os.path.sep + \
                         u'shifted_data.csv'
        self.output.setText(self.directory)

    def able_solve(self):
        """set Solve button enable"""

        if self.input.text() and self.output.text() and self.value.text():
            self.solve.setEnabled(True)
        else:
            self.solve.setEnabled(False)

    def able_show(self):
        """set showInput button enable"""

        if self.input.text():
            self.showInput.setEnabled(True)
        else:
            self.showInput.setEnabled(False)

    def solve_clicked(self):
        """call computing"""

        if self.computationRunning is not True:
            self.start_computing()

    def show_input(self):
        """show input csv as layer"""

        show_as_layer.show(self.input.text(), self.stylePath)

    def select_ellipsoid(self):
        """raise a dialog to choose the desired ellipsoid"""

        projSelector = QgsGenericProjectionSelector()
        projSelector.exec_()

        crs = QgsCoordinateReferenceSystem()
        crs.createFromSrsId(projSelector.selectedCrsId())

        if crs.isValid():
            if crs.ellipsoidAcronym() != '':
                self.ellipsoidSelector.setText(crs.ellipsoidAcronym())
            else:
                self.ellipsoidSelector.setText('WGS84')

    def start_computing(self):
        """computing called in new thread and showing a progressBar"""

        computation = Move(self.input.text(), self.output.text(),
                      self.ellipsoidSelector.text(), self.units.currentText(),
                      self.value.text())

        messageBar = self.iface.messageBar().createMessage('Computing...')
        progressBar = QtGui.QProgressBar()
        cancelButton = QtGui.QPushButton()
        cancelButton.setText('Cancel')
        messageBar.layout().addWidget(progressBar)
        messageBar.layout().addWidget(cancelButton)

        computationThread = QThread(self)
        computation.moveToThread(computationThread)
        computation.finished.connect(self.computing_finished)
        computation.progress.connect(progressBar.setValue)
        cancelButton.clicked.connect(self.cancel_computing)
        computationThread.started.connect(computation.shift)
        computation.error.connect(self.value_error)

        self.iface.messageBar().pushWidget(messageBar,
                                           self.iface.messageBar().INFO)

        if not computationThread.isRunning():
            self.computationRunning = True
            computationThread.start()

        self.computation = computation
        self.computationThread = computationThread
        self.messageBar = messageBar

    def computing_finished(self):
        """show new layer and clean up after threads"""

        if self.computation.abort is not True:
            show_as_layer.show(self.output.text(), self.stylePath)

        self.computation.deleteLater()
        self.computationThread.quit()
        self.computationThread.wait()
        self.computationThread.deleteLater()
        self.iface.messageBar().popWidget(self.messageBar)

        self.computationRunning = False

    def cancel_computing(self):
        """clicked on the Cancel button in messageBar"""

        self.computation.abort = True
        os.remove(self.output.text())

    def value_error(self, e):
        """error in input values"""

        QtGui.QMessageBox.critical(None,
                             "ERROR: Invalid number of values",
                             "{0}".format(e), QtGui.QMessageBox.Abort)

        self.computation.deleteLater()
        self.computationThread.quit()
        self.computationThread.wait()
        self.computationThread.deleteLater()
        self.iface.messageBar().popWidget(self.messageBar)

        self.computationRunning = False

    def close_event(self, event):  # closeEvent

        self.closingPlugin.emit()
        event.accept()
