"""
The lockbox widget is composed of all the submodules widgets
"""
from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
import logging
import numpy as np
from ..attribute_widgets import BaseAttributeWidget
from .base_module_widget import ReducedModuleWidget, ModuleWidget
from ...pyrpl_utils import get_base_module_class


APP = QtGui.QApplication.instance()


class AnalogTfDialog(QtGui.QDialog):
    def __init__(self, parent):
        super(AnalogTfDialog, self).__init__(parent)
        self.parent = parent
        self.module = self.parent.module
        self.setWindowTitle("Analog transfer function for output %s" % self.module.name)
        self.lay_v = QtGui.QVBoxLayout(self)
        self.lay_h = QtGui.QHBoxLayout()
        self.ok = QtGui.QPushButton('Ok')
        self.lay_h.addWidget(self.ok)
        self.ok.clicked.connect(self.validate)
        self.cancel = QtGui.QPushButton('Cancel')
        self.lay_h.addWidget(self.cancel)
        self.group = QtGui.QButtonGroup()
        self.flat = QtGui.QRadioButton("Flat response")
        self.filter = QtGui.QRadioButton('Analog low-pass filter (as in "Pid control/assisted design/analog filter cut-off")')
        self.curve = QtGui.QRadioButton("User-defined curve")
        self.group.addButton(self.flat)
        self.group.addButton(self.filter)
        self.group.addButton(self.curve)

        self.lay_v.addWidget(self.flat)
        self.lay_v.addWidget(self.filter)
        self.lay_v.addWidget(self.curve)
        self.label = QtGui.QLabel("Curve #")
        self.line = QtGui.QLineEdit("coucou")

        self.lay_line = QtGui.QHBoxLayout()
        self.lay_v.addLayout(self.lay_line)
        self.lay_v.addWidget(self.line)
        self.lay_line.addStretch(1)
        self.lay_line.addWidget(self.label)
        self.lay_line.addWidget(self.line, stretch=10)
        self.lay_v.addSpacing(20)
        self.lay_v.addLayout(self.lay_h)
        self.curve.toggled.connect(self.change_visibility)
        {'flat':self.flat, 'filter':self.filter, 'curve':self.curve}[self.module.tf_type].setChecked(True)

        self.line.setText(str(self.module.tf_curve))
        self.line.textEdited.connect(lambda: self.line.setStyleSheet(""))
        self.cancel.clicked.connect(self.reject)
        self.curve_id = None
        self.res = None

    def change_visibility(self, checked):
        for widget in self.label, self.line:
            widget.setEnabled(checked)

    def validate(self):
        self.line.setStyleSheet('')
        if self.flat.isChecked():
            self.res = "flat"
            self.accept()
        if self.filter.isChecked():
            self.res = 'filter'
            self.accept()
        if self.curve.isChecked():
            try:
                curve_id = int(str(self.line.text()))
            except:
                self.line.setStyleSheet('background-color:red;')
            else:
                self.res = 'curve'
                self.curve_id = curve_id
                self.accept()

    def get_type_number(self):
        accept = self.exec_()
        return accept, self.res, self.curve_id


class AnalogTfSpec(QtGui.QWidget):
    """
    A button + label that allows to display and change the transfer function specification
    """
    def __init__(self, parent):
        super(AnalogTfSpec, self).__init__(parent)
        self.parent = parent
        self.module = self.parent.module
        self.layout = QtGui.QVBoxLayout(self)
        self.label = QtGui.QLabel("Analog transfer function")
        self.layout.addWidget(self.label)
        self.button = QtGui.QPushButton('Change...')
        self.layout.addWidget(self.button)
        self.button.clicked.connect(self.change)
        self.dialog = AnalogTfDialog(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.change_analog_tf()

    def change(self, ev):
        accept, typ, number = self.dialog.get_type_number()
        if accept:
            if typ=='curve':
                self.module.tf_curve = number
            self.module.tf_type = typ
            self.change_analog_tf()

    def change_analog_tf(self):
        typ = self.module.tf_type
        try:
            txt = {'flat': 'flat', 'filter': 'low-pass', 'curve': 'user curve'}[typ]
        except KeyError:
            txt = typ
        if typ=='curve':
            txt += ' #' + str(self.module.tf_curve)
        self.button.setText(txt)


class MainOutputProperties(QtGui.QGroupBox):
    def __init__(self, parent):
        super(MainOutputProperties, self).__init__(parent)
        self.parent = parent
        self.module = self.parent.module
        aws = self.parent.attribute_widgets
        self.layout = QtGui.QHBoxLayout(self)
        self.leftlayout = QtGui.QVBoxLayout(self)
        self.rightlayout = QtGui.QVBoxLayout(self)
        self.layout.addLayout(self.leftlayout)
        self.layout.addLayout(self.rightlayout)
        self.v1 = QtGui.QHBoxLayout()
        self.v2 = QtGui.QHBoxLayout()
        self.leftlayout.addLayout(self.v2)
        self.leftlayout.addLayout(self.v1)
        self.dcgain = aws['dc_gain']
        self.v1.addWidget(self.dcgain)
        self.dcgain.label.setText('analog DC-gain')
        self.v1.addWidget(aws["unit"])
        aws['dc_gain'].set_log_increment()
        self.v2.addWidget(aws["output_channel"])
        # self.v2.addWidget(aws["tf_type"])
        self.button_tf = AnalogTfSpec(self)
        self.v2.addWidget(self.button_tf)
        # aws['tf_curve'].hide()
        self.setTitle('Main settings')
        for v in self.v1, self.v2:
            v.setSpacing(9)
        self.rightlayout.addWidget(aws["max_voltage"])
        self.rightlayout.addWidget(aws["min_voltage"])

    def change_analog_tf(self):
        self.button_tf.change_analog_tf()


class SweepOutputProperties(QtGui.QGroupBox):
    def __init__(self, parent):
        super(SweepOutputProperties, self).__init__(parent)
        self.parent = parent
        aws = self.parent.attribute_widgets
        self.layout = QtGui.QHBoxLayout(self)
        self.v1 = QtGui.QVBoxLayout()
        self.layout.addLayout(self.v1)
        self.v2 = QtGui.QVBoxLayout()
        self.layout.addLayout(self.v2)
        self.v1.addWidget(aws["sweep_frequency"])
        self.v1.addWidget(aws['sweep_amplitude'])
        self.v2.addWidget(aws["sweep_offset"])
        self.v2.addWidget(aws["sweep_waveform"])
        self.setTitle("Sweep parameters")

class WidgetManual(QtGui.QWidget):
    def __init__(self, parent):
        super(WidgetManual, self).__init__(parent)
        self.parent = parent
        self.layout = QtGui.QVBoxLayout(self)
        self.pv1 = QtGui.QVBoxLayout()
        self.pv2 = QtGui.QVBoxLayout()
        self.layout.addLayout(self.pv1)
        self.layout.addLayout(self.pv2)
        self.p = parent.parent.attribute_widgets["p"]
        self.i = parent.parent.attribute_widgets["i"]

        self.p.label.setText('proportional gain (1)')
        self.i.label.setText('integral unity-gain (Hz)')
        #self.p.label.setFixedWidth(24)
        #self.i.label.setFixedWidth(24)
        # self.p.adjustSize()
        # self.i.adjustSize()
        for prop in self.p, self.i:
            prop.widget.set_log_increment()
        self.pv1.addWidget(self.p)
        self.pv2.addWidget(self.i)
        # self.i.label.setMinimumWidth(6)

class WidgetAssisted(QtGui.QWidget):
    def __init__(self, parent):
        super(WidgetAssisted, self).__init__(parent)
        self.parent = parent
        self.layout = QtGui.QVBoxLayout(self)
        self.v1 = QtGui.QVBoxLayout()
        self.v2 = QtGui.QVBoxLayout()
        self.layout.addLayout(self.v1)
        self.layout.addLayout(self.v2)
        self.desired = parent.parent.attribute_widgets["desired_unity_gain_frequency"]
        self.desired.label.setText('desired unity-gain-frequency (Hz) ')
        self.desired.set_log_increment()
        self.analog_filter = parent.parent.attribute_widgets["analog_filter_cutoff"]
        self.analog_filter.label.setText('analog filter cut-off frequency (Hz)')
        #self.analog_filter.set_horizontal()
        # self.analog_filter.layout_v.setSpacing(0)
        # self.analog_filter.layout_v.setContentsMargins(0, 0, 0, 0)
        #self.analog_filter.set_max_cols(2)
        self.v1.addWidget(self.desired)
        self.v2.addWidget(self.analog_filter)


class PidProperties(QtGui.QGroupBox):
    def __init__(self, parent):
        super(PidProperties, self).__init__(parent)
        self.parent = parent
        self.module = self.parent.module
        aws = self.parent.attribute_widgets
        self.layout = QtGui.QHBoxLayout(self)
        self.v2 = QtGui.QVBoxLayout()
        self.layout.addLayout(self.v2)
        self.v1 = QtGui.QVBoxLayout()
        self.layout.addLayout(self.v1)

        self.radio_group = QtGui.QButtonGroup()
        self.manual = QtGui.QRadioButton('manual design')
        self.assisted = QtGui.QRadioButton('assisted design')
        self.radio_group.addButton(self.manual)
        self.radio_group.addButton(self.assisted)
        self.assisted.toggled.connect(self.toggle_mode)
        # only one button of the group must be connected
        # self.manual.toggled.connect(self.toggle_mode)

        self.manual_widget = WidgetManual(self)
        self.v1.addWidget(self.manual)
        self.v1.addWidget(self.manual_widget)
        # self.col3.addWidget(aws["tf_filter"])

        self.assisted_widget = WidgetAssisted(self)
        self.v2.insertWidget(0, self.assisted)
        self.v2.addWidget(self.assisted_widget)
        self.v2.addStretch(5)

        self.setTitle("Pid control")

        for v in (self.v1, self.v2, self.layout):
            v.setSpacing(0)
            v.setContentsMargins(5, 1, 0, 0)

    def toggle_mode(self): # manual vs assisted design button clicked
        if self.manual.isChecked():
            self.module.assisted_design = False
        else:
            self.module.assisted_design = True
        self.update_assisted_design()

    def update_assisted_design(self):
        """
        Does what must be done when manual/assisted design radio button was clicked
        """
        assisted_on = self.module.assisted_design
        self.blockSignals(True)
        try:
            self.manual.setChecked(not assisted_on)
            self.assisted.setChecked(assisted_on)
            self.manual_widget.setEnabled(not assisted_on)
            self.assisted_widget.setEnabled(assisted_on)
        finally:
            self.blockSignals(False)


class PostFiltering(QtGui.QGroupBox):
    def __init__(self, parent):
        super(PostFiltering, self).__init__(parent)
        self.parent = parent
        aws = self.parent.attribute_widgets
        self.layout = QtGui.QVBoxLayout(self)

        aws = self.parent.attribute_widgets
        self.layout.addWidget(aws["additional_filter"])

        self.mod_layout = QtGui.QHBoxLayout()
        self.mod_layout.addWidget(aws["extra_module"])
        self.mod_layout.addWidget(aws["extra_module_state"])
        self.layout.addLayout(self.mod_layout)
        self.layout.setSpacing(12)

        self.setTitle("Pre-filtering before PID")


class OutputSignalWidget(ModuleWidget):
    @property
    def name(self):
        return self.module.name

    @name.setter
    def name(self, value):
        # name is read-only
        pass

    def change_analog_tf(self):
        self.main_props.change_analog_tf()

    def init_gui(self):
        self.main_layout = QtGui.QVBoxLayout()
        self.setLayout(self.main_layout)
        self.init_attribute_layout()
        for widget in self.attribute_widgets.values():
            self.main_layout.removeWidget(widget)
        self.upper_layout = QtGui.QHBoxLayout()
        self.main_layout.addLayout(self.upper_layout)
        self.col1 = QtGui.QVBoxLayout()
        self.col2 = QtGui.QVBoxLayout()
        self.col3 = QtGui.QVBoxLayout()
        self.col4 = QtGui.QVBoxLayout()
        self.upper_layout.addStretch(1)
        self.upper_layout.addLayout(self.col1)
        self.upper_layout.addStretch(1)
        self.upper_layout.addLayout(self.col2)
        self.upper_layout.addStretch(1)
        self.upper_layout.addLayout(self.col3)
        self.upper_layout.addStretch(1)
        self.upper_layout.addLayout(self.col4)
        self.upper_layout.addStretch(1)

        aws = self.attribute_widgets
        self.main_props = MainOutputProperties(self)
        self.col1.addWidget(self.main_props)
        self.col1.addStretch(5)

        self.sweep_props = SweepOutputProperties(self)
        self.col2.addWidget(self.sweep_props)
        self.col2.addStretch(5)

        self.pid_props = PidProperties(self)
        self.pid_props.update_assisted_design()
        self.col3.addWidget(self.pid_props)

        self.col3.addStretch(5)

        self.post_props = PostFiltering(self)
        self.col4.addWidget(self.post_props)

        self.col4.addStretch(5)

        self.win = pg.GraphicsWindow(title="Amplitude")
        self.win_phase = pg.GraphicsWindow(title="Phase")
        self.plot_item = self.win.addPlot(title="Magnitude (dB)")
        self.plot_item_phase = self.win_phase.addPlot(title="Phase (deg)")
        self.plot_item.showGrid(y=True, x=True, alpha=1.)
        self.plot_item_phase.showGrid(y=True, x=True, alpha=1.)

        self.plot_item_phase.setXLink(self.plot_item)

        self.curve = self.plot_item.plot(pen='y')
        self.curve_phase = self.plot_item_phase.plot(pen=None, symbol='o', symbolSize=1)

        self.plot_item.setLogMode(x=True, y=True)
        self.plot_item_phase.setLogMode(x=True, y=None)
        self.curve.setLogMode(xMode=True, yMode=True)
        self.curve_phase.setLogMode(xMode=True, yMode=None)

        self.plotbox = QtGui.QGroupBox(self)
        self.plotbox.layout = QtGui.QVBoxLayout(self.plotbox)
        self.plotbox.setTitle("Complete open-loop transfer function (V/V)")
        self.plotbox.layout.addWidget(self.win)
        self.plotbox.layout.addWidget(self.win_phase)
        self.main_layout.addWidget(self.plotbox)
        self.update_transfer_function()

    def update_transfer_function(self):
        """
        Updates the transfer function curve of the output.
        """
        freqs = self.module.tf_freqs()
        curve = self.module.transfer_function(freqs)
        abs_curve = abs(curve)
        if(max(abs_curve)>0): # python 2 crashes when plotting zeros in log_mode
            self.curve.setData(freqs, abs_curve)
            self.curve_phase.setData(freqs, 180./np.pi*np.angle(curve))


class LockboxInputWidget(ModuleWidget):
    """
    A widget to represent a single lockbox input
    """
    def init_gui(self):
        self.main_layout = QtGui.QVBoxLayout(self)
        self.init_attribute_layout()

        self.win = pg.GraphicsWindow(title="Expected signal")
        self.plot_item = self.win.addPlot(title='Expected ' + self.module.name)
        self.plot_item.showGrid(y=True, x=True, alpha=1.)
        self.curve = self.plot_item.plot(pen='y')
        self.curve_slope = self.plot_item.plot(pen=pg.mkPen('b', width=5))
        self.symbol = self.plot_item.plot(pen='b', symbol='o')
        self.main_layout.addWidget(self.win)
        self.button_calibrate = QtGui.QPushButton('Calibrate')
        self.main_layout.addWidget(self.button_calibrate)
        self.button_calibrate.clicked.connect(lambda: self.module.calibrate())
        self.update_expected_signal()

    def hide_lock(self):
        self.curve_slope.setData([], [])
        self.symbol.setData([], [])
        self.plot_item.enableAutoRange(enable=True)

    def show_lock(self, input, variable_value):
        signal = self.module.expected_signal(variable_value)
        slope = self.module.expected_slope(variable_value)
        dx = 1
        self.plot_item.enableAutoRange(enable=False)
        self.curve_slope.setData([variable_value - dx, variable_value + dx],
                                 [signal - slope * dx, signal + slope*dx])
        self.symbol.setData([variable_value], [signal])

    def show_graph(self, x, y):
        """
        x, y are two 1D arrays.
        """
        self.curve.setData(x, y)

    def update_expected_signal(self, input=None):
        # if input is None, input associated with this widget is used
        if input is None:
            input = self.module
        y = input.expected_signal(input.plot_range)
        self.show_graph(input.plot_range, y)


class InputsWidget(QtGui.QWidget):
    """
    A widget to represent all input signals on the same tab
    """
    name = 'inputs'
    def __init__(self, all_sig_widget):
        self.all_sig_widget = all_sig_widget
        self.lb_widget = self.all_sig_widget.lb_widget
        super(InputsWidget, self).__init__(all_sig_widget)
        self.layout = QtGui.QHBoxLayout(self)
        self.input_widgets = []
        #self.layout.addStretch(1)
        for signal in self.lb_widget.module.inputs:
            self.add_input(signal)
        #self.layout.addStretch(1)

    def remove_input(self, input):
        for widget in self.input_widgets:
            if widget.name == input.name:
                widget.hide()
                self.input_widgets.remove(widget)
                widget.deleteLater()

    def add_input(self, input):
        widget = input._create_widget()
        self.input_widgets.append(widget)
        self.layout.addWidget(widget, stretch=3)

    def update_expected_input_signal(self, input):
        for widget in self.input_widgets:
            if widget.name==input.name:
                widget.update_expected_signal(input)

    def show_lock(self, stage):
        for widget in self.input_widgets:
            try:
                if widget.name==stage.input:
                    widget.show_lock(stage.input, stage.setpoint)
            except AttributeError:  # when stage is not a Stage object
                pass


class PlusTab(QtGui.QWidget):
    name = '+'


class MyTabBar(QtGui.QTabBar):
    def tabSizeHint(self, index):
        """
        Tab '+' and 'inputs' are smaller since they don't have a close button
        """
        size = super(MyTabBar, self).tabSizeHint(index)
        #if index==0 or index==self.parent().count() - 1:
        #    return QtCore.QSize(size.width() - 15, size.height())
        #else:
        return size


class AllSignalsWidget(QtGui.QTabWidget):
    """
    A tab widget combining all inputs and outputs of the lockbox
    """
    def __init__(self, lockbox_widget):
        super(AllSignalsWidget, self).__init__()
        self.tab_bar = MyTabBar()
        self.setTabBar(self.tab_bar)
        self.setTabsClosable(True)
        self.tabBar().setSelectionBehaviorOnRemove(QtGui.QTabBar.SelectLeftTab) # otherwise + tab could be selected by
        # removing previous tab
        self.output_widgets = []
        self.lb_widget = lockbox_widget
        self.inputs_widget = InputsWidget(self)
        self.addTab(self.inputs_widget, "inputs")
        self.tabBar().tabButton(0, QtGui.QTabBar.RightSide).resize(0, 0) # hide "close" for "inputs" tab
        self.tab_plus = PlusTab()  # dummy widget that will never be displayed
        self.addTab(self.tab_plus, "+")
        self.tabBar().tabButton(self.count() - 1, QtGui.QTabBar.RightSide).resize(0, 0)  # hide "close" for "+" tab
        for signal in self.lb_widget.module.outputs:
            self.add_output(signal)
        self.currentChanged.connect(self.tab_changed)
        self.tabCloseRequested.connect(self.close_tab)
        self.update_output_names()

    def tab_changed(self, index):
        if index==self.count()-1: # tab "+" clicked
            self.lb_widget.module._add_output()
            self.setCurrentIndex(self.count()-2) # bring created output tab on top

    def close_tab(self, index):
        lockbox = self.lb_widget.module
        lockbox._remove_output(lockbox.outputs[index - 1])

    ## Output Management
    def add_output(self, signal):
        """
        signal is an instance of OutputSignal
        """
        widget = signal._create_widget()
        self.output_widgets.append(widget)
        self.insertTab(self.count() - 1, widget, widget.name)

    def output_widget_names(self):
        return [widget.name for widget in self.output_widgets]

    def remove_output(self, output):
        for widget in self.output_widgets:
            if widget.module == output:
                self.output_widgets.remove(widget)
                widget.deleteLater()

    def update_output_names(self):
        for index in range(self.count()):
            widget = self.widget(index)
            if hasattr(widget, "module"):
                self.setTabText(index, widget.module.name)
            #if widge
            #if len(self.lb_widget.module.output_names)>=index:
            #    self.setTabText(index, self.lb_widget.module.output_names[
            #        index-1])

    def show_lock(self, stage):
        self.inputs_widget.show_lock(stage)

    ## Input Management
    def add_input(self, input):
        self.inputs_widget.add_input(input)

    def remove_input(self, input):
        self.inputs_widget.remove_input(input)

    def update_transfer_function(self, output):
        if output.name in self.output_widget_names():
            self.get_output_widget_by_name(
                output.name).update_transfer_function()

    def update_expected_input_signal(self, input):
        self.inputs_widget.update_expected_input_signal(input)

    def get_output_widget_by_name(self, name):
        for widget in self.output_widgets:
            if widget.module.name==name:
                return widget


class MyCloseButton(QtGui.QPushButton):
    def __init__(self, parent=None):
        super(MyCloseButton, self).__init__(parent)
        style = APP.style()
        close_icon = style.standardIcon(QtGui.QStyle.SP_TitleBarCloseButton)
        self.setIcon(close_icon)
        self.setFixedHeight(16)
        self.setFixedWidth(16)
        self.setToolTip("Delete this stage...")


class MyAddButton(QtGui.QPushButton):
    def __init__(self, parent=None):
        super(MyAddButton, self).__init__(parent)
        style = APP.style()
        close_icon = style.standardIcon(QtGui.QStyle.SP_TitleBarNormalButton)
        self.setIcon(close_icon)
        self.setFixedHeight(16)
        self.setFixedWidth(16)
        self.setToolTip("Add a new stage before this one...")


class StageOutputWidget(ReducedModuleWidget):
    def init_attribute_layout(self):
        super(StageOutputWidget, self).init_attribute_layout()
        # constrain the size of the offset
        self.attribute_widgets["offset"].resize(1, self.attribute_widgets["offset"].height())
        self.attribute_widgets["offset"].setFixedWidth(100)
        self.attribute_widgets["reset_offset"].setToolTip("Reset output offset value at the beginning of this stage?")


class LockboxStageWidget(ReducedModuleWidget):
    """
    A widget representing a single lockbox stage
    """
    @property
    def name(self):
        return '    stage '+str(self.module.name)

    @name.setter
    def name(self, value):
        pass

    def init_gui(self):
        self.main_layout = QtGui.QVBoxLayout(self)
        self.init_attribute_layout()
        for name, attr in self.attribute_widgets.items():
            self.attribute_layout.removeWidget(attr)
        self.lay_h1 = QtGui.QHBoxLayout()
        self.main_layout.addLayout(self.lay_h1)
        self.lay_v1 = QtGui.QVBoxLayout()
        self.lay_h1.addLayout(self.lay_v1)
        self.lay_v2 = QtGui.QVBoxLayout()
        self.lay_h1.addLayout(self.lay_v2)
        aws = self.attribute_widgets
        #self.lay_v1.addWidget(aws['name'])
        self.lay_v1.addWidget(aws['input'])
        self.lay_v2.addWidget(aws['setpoint'])
        self.lay_v1.addWidget(aws['duration'])
        self.lay_v2.addWidget(aws['gain_factor'])
        self.lay_h2 = QtGui.QVBoxLayout()
        self.main_layout.addLayout(self.lay_h2)
        for output in self.module.lockbox.outputs:
            self.lay_h2.addWidget(self.module.outputs[output.name]._create_widget())
        self.lay_h3 = QtGui.QHBoxLayout()
        self.main_layout.addLayout(self.lay_h3)
        self.lay_h3.addWidget(aws['function_call'])

        self.button_goto = QtGui.QPushButton('Go to this stage')
        self.button_goto.clicked.connect(self.module.enable)
        self.main_layout.addWidget(self.button_goto)

    def create_title_bar(self):
        super(LockboxStageWidget, self).create_title_bar()
        self.close_button = MyCloseButton(self)
        self.close_button.clicked.connect(self.close)
        self.close_button.move(self.width() - self.close_button.width(), self.title_pos[1] + 8)
        self.add_button = MyAddButton(self)
        self.add_button.clicked.connect(lambda: self.module.parent.insert(self.module.name,
                                                                          self.module.setup_attributes))
        self.add_button.move(0, self.title_pos[1] + 8)

    def resizeEvent(self, evt):
        super(LockboxStageWidget, self).resizeEvent(evt)
        self.close_button.move(evt.size().width() - self.close_button.width(), self.title_pos[1])
        self.add_button.move(0, self.title_pos[1])

    def close(self):
        self.module._logger.debug("Closing stage %s", self.module.name)
        if len(self.module.parent) == 1:
            self.module._logger.warning("You are not allowed to delete the last stage!")
        else:
            self.module.parent.remove(self.module)

    def show_lock(self):
        self.parent().parent().set_button_green(self.button_goto)


class LockboxSequenceWidget(ModuleWidget):
    """
    A widget to represent all lockbox stages
    """
    def init_gui(self):
        self.main_layout = QtGui.QHBoxLayout(self)
        self.init_attribute_layout()
        self.stage_widgets = []
        self.button_add = QtGui.QPushButton('+')
        self.button_add.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
        #self.button_add.setMinimumHeight(60)
        self.button_add.clicked.connect(lambda: self.module.append(self.module[-1].setup_attributes))
        self.main_layout.addWidget(self.button_add)
        for stage in self.module:
            self.stage_created([stage])
        self.main_layout.addStretch(2)

    def stage_created(self, stage):
        stage = stage[0] # values are passed as list of length 1
        widget = stage._create_widget()
        stage._widget = widget
        self.stage_widgets.insert(stage.name, widget)
        if stage.name >= len(self.stage_widgets)-1:
            # stage must be inserted at the end
            insert_before = self.button_add
        else:
            # stage was inserted before another one
            insert_before = self.stage_widgets[self.stage_widgets.index(widget)+1]
        self.main_layout.insertWidget(self.main_layout.indexOf(insert_before), widget)
        self.update_stage_names()

    def stage_deleted(self, stage):
        """ removes the widget corresponding to stage"""
        stage = stage[0] # values are passes as list of length 1
        widget = stage._widget
        self.stage_widgets.remove(widget)
        if self.parent().parent().parent().button_green == widget.button_goto:
            self.parent().parent().parent().button_green = None
        widget.hide()
        self.main_layout.removeWidget(widget)
        widget.deleteLater()
        self.update_stage_names()

    def update_stage_names(self):
        for widget in self.stage_widgets:
            widget.set_title(widget.name)


class LockboxWidget(ModuleWidget):
    """
    The LockboxWidget combines the lockbox submodules widget: model, inputs, outputs, lockbox_control
    """
    def init_gui(self):
        # make standard layout
        self.main_layout = QtGui.QVBoxLayout()
        self.setLayout(self.main_layout)  # wasnt here before
        self.init_attribute_layout()
        # move all custom attributes to the second GUI line (spares place)
        self.custom_attribute_layout = QtGui.QHBoxLayout()
        self.main_layout.addLayout(self.custom_attribute_layout)
        lockbox_base_class = get_base_module_class(self.module)
        for attr_name in self.module._gui_attributes:
            if attr_name not in lockbox_base_class._gui_attributes:
                widget = self.attribute_widgets[attr_name]
                self.attribute_layout.removeWidget(widget)
                self.custom_attribute_layout.addWidget(widget)
        # add buttons to standard attribute layout
        self.button_is_locked = QtGui.QPushButton("is_locked?")
        self.button_lock = QtGui.QPushButton("Lock")
        self.button_unlock = QtGui.QPushButton("Unlock")
        self.button_sweep = QtGui.QPushButton("Sweep")
        self.button_calibrate_all = QtGui.QPushButton("Calibrate all inputs")
        self.button_green = self.button_unlock
        self.set_button_green(self.button_green)
        self.attribute_layout.addWidget(self.button_is_locked)
        self.attribute_layout.addWidget(self.button_lock)
        self.attribute_layout.addWidget(self.button_unlock)
        self.attribute_layout.addWidget(self.button_sweep)
        self.attribute_layout.addWidget(self.button_calibrate_all)
        self.button_is_locked.clicked.connect(lambda: self.module.is_locked(
            loglevel=self.module._logger.getEffectiveLevel()))
        self.button_lock.clicked.connect(lambda: self.module.lock())
        self.button_unlock.clicked.connect(lambda: self.module.unlock())
        self.button_sweep.clicked.connect(lambda: self.module.sweep())
        self.button_calibrate_all.clicked.connect(lambda: self.module.calibrate_all())

        # Locking sequence widget + hide button
        self.sequence_widget = self.module.sequence._create_widget()
        self.scrollarea = QtGui.QScrollArea()
        self.scrollarea.setWidget(self.sequence_widget)
        minimumsizehint = self.sequence_widget.minimumSizeHint().height() \
                         + self.scrollarea.horizontalScrollBar().height()
        self.scrollarea.setMinimumHeight(minimumsizehint)
        #self.scrollarea.setVerticalScrollBarPolicy(
        #    QtCore.Qt.ScrollBarAlwaysOff)
        #self.sequence_widget.setSizePolicy(QtGui.QSizePolicy.Preferred,
        #                                   QtGui.QSizePolicy.Preferred)
        self.scrollarea.setWidgetResizable(True)
        self.main_layout.addWidget(self.scrollarea)
        # hide button for sequence
        # self.button_hide1 = QtGui.QPushButton("^ Lock sequence ^")
        # self.button_hide1.setMaximumHeight(15)
        # self.button_hide1.clicked.connect(self.button_hide1_clicked)
        # self.main_layout.addWidget(self.button_hide1)

        # inputs/ outputs widget
        self.all_sig_widget = AllSignalsWidget(self)
        self.button_hide2 = QtGui.QPushButton("hide inputs / outputs")
        #self.button_hide_clicked() # open by default
        self.button_hide2.setMaximumHeight(15)
        #self.button_hide2.setMaximumWidth(150)
        self.button_hide2.clicked.connect(self.button_hide2_clicked)
        self.main_layout.addWidget(self.button_hide2)
        self.main_layout.addWidget(self.all_sig_widget)

        self.main_layout.addStretch(5)
        self.setLayout(self.main_layout)

    def delete_widget(self):
        self.module = None  # allow module to be deleted
        self.deleteLater()

    def button_hide1_clicked(self):
        """
        Hide/show the signal part of the widget
        :return:
        """
        current = str(self.button_hide1.text())
        if current.endswith('v'):
            self.button_hide1.setText('^' + current[1:-1] + '^')
            self.sequence_widget.show()
        else:
            self.button_hide1.setText('v' + current[1:-1] + 'v')
            self.sequence_widget.hide()

    def button_hide2_clicked(self):
        """
        Hide/show the signal part of the widget
        :return:
        """
        # current = str(self.button_hide2.text())
        # if current.endswith('v'):
        #     self.button_hide2.setText('^' + current[1:-1] + '^')
        #     self.all_sig_widget.show()
        # else:
        #     self.button_hide2.setText('v' + current[1:-1] + 'v')
        #     self.all_sig_widget.hide()
        current = str(self.button_hide2.text())
        if current.startswith('show'):
            self.button_hide2.setText('hide' + current[4:])
            self.all_sig_widget.show()
        else:
            self.button_hide2.setText('show' + current[4:])
            self.all_sig_widget.hide()

    def input_calibrated(self, inputs):
        """
        SLOT: don't change name unless you know what you are doing
        updates the plot of the input expected signal for input inputs[0]
        """
        for input in inputs:
            self.all_sig_widget.update_expected_input_signal(input)

    def update_transfer_function(self, outputs):
        """
        SLOT: don't change name unless you know what you are doing
        updates the plot of the transfer function for output outputs[0]
        """
        self.all_sig_widget.update_transfer_function(outputs[0])

    ## Input Management
    def add_input(self, inputs):
        """
        SLOT: don't change name unless you know what you are doing
        Adds an input to the widget
        """
        self.all_sig_widget.add_input(inputs[0])

    def remove_input(self, inputs):
        """
        SLOT: don't change name unless you know what you are doing
        Remove an input to the widget
        """
        self.all_sig_widget.remove_input(inputs[0])

    ## Output Management
    def output_renamed(self):
        """
        SLOT: don't change name unless you know what you are doing
        Refresh all output name tabs in the widget
        """
        self.all_sig_widget.update_output_names()

    def output_created(self, outputs):
        """
        SLOT: don't change name unless you know what you are doing
        Adds an output to the widget,  outputs is a singleton [outpout]
        """
        self.all_sig_widget.add_output(outputs[0])

    def output_deleted(self, outputs):
        """
        SLOT: don't change name unless you know what you are doing
        Removes an output to the widget, outputs is a singleton [outpout]
        """
        self.all_sig_widget.remove_output(outputs[0])

    def state_changed(self):
        """
        SLOT: don't change name unless you know what you are doing
        Basically painting some button in green is required
        """
        stage = self.module.current_stage
        if stage=='unlock':
            self.set_button_green(self.button_unlock)
            self.hide_lock_points()
        elif stage=='sweep':
            self.hide_lock_points()
            self.set_button_green(self.button_sweep)
        else:
            try:
                self.set_button_green(stage._widget.button_goto)
            except AttributeError:  # if stage has not widget (final_stage)
                self.set_button_green(None)
            self.show_lock(stage)
        self.update_lockstatus()

    def set_button_green(self, button):
        """
        Only one colored button can exist at a time
        """
        if self.button_green is not None:
            self.button_green.setStyleSheet("")
        if button is not None:
            button.setStyleSheet("background-color:green")
        self.button_green = button

    def show_lock(self, stage):
        """
        The button of the stage widget becomes green, the expected signal graph of input show the lock point and slope.
        """
        self.hide_lock_points()
        if isinstance(stage, int):
            stage = self.module.sequence[stage]
        elif stage == "final_stage":
            stage = self.module.final_stage
        self.all_sig_widget.show_lock(stage)

    def hide_lock_points(self):
        """
        make sure all input graphs are not displaying any setpoints and slopes
        """
        for input_widget in self.all_sig_widget.inputs_widget.input_widgets:
            input_widget.hide_lock()

    def update_lockstatus(self, islockedlist=[None]):
        islocked = islockedlist[0]
        # color = self.module._is_locked_display_color
        color = self._is_locked_display_color(islocked=islocked)
        self.button_is_locked.setStyleSheet("background-color: %s; "
                                            "color:white"%color)

    def _is_locked_display_color(self, islocked=None):
        """ function that returns the color of the LED indicating
        lockstatus. If is_locked is called in update_lockstatus above,
        it should not be called a second time here
        """
        module = self.module
        if module.current_state == 'sweep':
            return 'blue'
        elif module.current_state == 'unlock':
            return 'darkRed'
        else:
            # should be locked
            if islocked is None:
                islocked = module.is_locked(loglevel=logging.DEBUG)
            if islocked:
                if module.current_stage == module.final_stage:
                    # locked and in last stage
                    return 'green'
                else:
                    # locked but acquiring
                    return 'yellow'
            else:
                # unlocked but not supposed to
                return 'red'
