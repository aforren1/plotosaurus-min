import argparse

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from toon.input import MpDevice, stack
from hand import Hand, get_teensy_path
from demo_dev import SingleResp


class LivePlot(pg.GraphicsLayoutWidget):
    def __init__(self, device):
        super(LivePlot, self).__init__()
        self.device = MpDevice(device)
        self.current_data = None
        self.figs = []
        self.lines = []
        dummy = np.ones(15)
        for i in range(5):
            self.figs.append(self.addPlot(title='Finger %s' % (i + 1)))
            self.figs[i].showGrid(x=True, y=True, alpha=0.4)
            self.figs[i].setClipToView(True)
            self.figs[i].setRange(yRange=[-0.5, 0.5])
            self.figs[i].setLimits(yMin=-0.5, yMax=0.5)
            for j in range(3):
                pen = pg.mkPen(color=pg.intColor(j, hues=5, alpha=220), width=3)
                self.lines.append(self.figs[i].plot(dummy, dummy, pen=pen))
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(0)
        self.playing = True

    def update(self):
        pos = self.device.read()
        if pos is None:
            return
        if self.current_data is None:
            self.current_data = pos
            self.current_time = pos.time
        elif self.current_data.shape[0] < self.device.device.sampling_frequency:
            self.current_data = np.vstack((self.current_data, pos))
            self.current_time = np.hstack((self.current_time, pos.time))
        else:
            ps0 = -pos.shape[0]
            self.current_data = np.roll(self.current_data, ps0, axis=0)
            self.current_data[ps0:, :] = pos
            self.current_time = np.roll(self.current_time, ps0)
            self.current_time[ps0:] = pos.time
        if self.playing:
            for counter, line in enumerate(self.lines):
                line.setData(y=self.current_data[:, counter])


if __name__ == '__main__':
    from warnings import warn
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', default=False,
                        action='store_true', help='Demo mode?')
    args = parser.parse_args()
    if args.demo:
        # demo device
        device = SingleResp()
    else:
        try:
            get_teensy_path(None)
            device = Hand()
        except StopIteration:
            warn('Device not found, using demo mode.')
            device = SingleResp()

    app = QtGui.QApplication([])
    w = QtGui.QWidget()
    liveplot = LivePlot(device)

    pause_button = QtGui.QPushButton('Pause')

    def on_click():
        liveplot.playing = not liveplot.playing

    pause_button.clicked.connect(on_click)
    layout = QtGui.QGridLayout()
    w.setLayout(layout)
    layout.addWidget(liveplot, 0, 0, 3, 3)
    layout.addWidget(pause_button, 0, 1)
    w.setGeometry(10, 10, 1600, 600)
    w.show()
    with liveplot.device:
        app.exec_()
