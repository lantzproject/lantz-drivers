from PyQt5 import QtCore
import ctypes

from lantz.driver import Driver

xinput = ctypes.windll.xinput9_1_0

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ('buttons', ctypes.c_ushort),
        ('left_trigger', ctypes.c_ubyte),
        ('right_trigger', ctypes.c_ubyte),
        ('l_thumb_x', ctypes.c_short),
        ('l_thumb_y', ctypes.c_short),
        ('r_thumb_x', ctypes.c_short),
        ('r_thumb_y', ctypes.c_short),
    ]

class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ('packet_number', ctypes.c_ulong),
        ('gamepad', XINPUT_GAMEPAD),
    ]

class XINPUT_VIBRATION(ctypes.Structure):
    _fields_ = [
        ('wLeftMotorSpeed', ctypes.c_ushort),
        ('wRightMotorSpeed', ctypes.c_ushort),
    ]

def val_to_bits(value, nbits=16):
    return [int(v) for v in bin(value)[2:].zfill(nbits)]

ERROR_DEVICE_NOT_CONNECTED = 1167
ERROR_SUCCESS = 0

class _XInputController(QtCore.QObject):

    max_devices = 4

    on_axis = QtCore.pyqtSignal(str, float)
    on_button = QtCore.pyqtSignal(int, bool)

    def __init__(self, device_number, input_deadzone=0.01):
        self.device_number = device_number
        self.input_deadzone = input_deadzone
        super().__init__()
        self._last_state = self.get_state()
        return

    @staticmethod
    def enumerate_devices():
        devices = (XInputController(device_id)
                   for device_id in range(XInputController.max_devices))
        return [d for d in devices if d.is_connected()]

    def normalize(self, value, sizeof_ctype):
        bitsof_ctype = 8 * sizeof_ctype
        return value / (2 ** bitsof_ctype - 1)

    def is_connected(self):
        return self._last_state is not None

    def set_vibration(self, left_motor, right_motor):
        XInputSetState = xinput.XInputSetState
        XInputSetState.argtypes = [ctypes.c_uint, ctypes.POINTER(XINPUT_VIBRATION)]
        XInputSetState.restype = ctypes.c_uint

        left_value = int(left_motor * 65535)
        right_value = int(right_motor * 65535)
        vibration = XINPUT_VIBRATION(left_value, right_value)
        XInputSetState(self.device_number, ctypes.byref(vibration))
        return

    def get_state(self):
        state = XINPUT_STATE()
        result = xinput.XInputGetState(self.device_number, ctypes.byref(state))
        if result == ERROR_SUCCESS:
            return state
        elif result == ERROR_DEVICE_NOT_CONNECTED:
            return None
        else:
            raise RuntimeError()

    def dispatch_events(self):
        state = self.get_state()
        if state is None:
            raise RuntimeError()
        if self._last_state is not None and state.packet_number != self._last_state.packet_number:
            self.handle_changed_state(state)
        self._last_state = state
        return
        
    def handle_changed_state(self, state):
        self.dispatch_axis_events(state)
        self.dispatch_button_events(state)
        return

    def dispatch_axis_events(self, state):
        axis_fields = dict(XINPUT_GAMEPAD._fields_)
        axis_fields.pop('buttons')
        for axis, ctype in axis_fields.items():
            old_value = getattr(self._last_state.gamepad, axis)
            new_value = getattr(state.gamepad, axis)
            sizeof_ctype = ctypes.sizeof(ctype)
            old_value = self.normalize(old_value, sizeof_ctype)
            new_value = self.normalize(new_value, sizeof_ctype)
            d_value = abs(new_value - old_value)
            if d_value:
                self.on_axis.emit(axis, new_value)

    def dispatch_button_events(self, state):
        changed = state.gamepad.buttons ^ self._last_state.gamepad.buttons
        changed_bits = val_to_bits(changed)
        state_bits = val_to_bits(state.gamepad.buttons)
        button_numbers = range(1, 17)
        changed_buttons = [(bn, bs) for changed, bn, bs in zip(changed_bits, button_numbers, state_bits)
                           if changed]
        [self.on_button.emit(button, bool(pressed)) for button, pressed in changed_buttons]
        return

    def axis_event(self, axis, value):
        pass

    def button_event(self, button, pressed):
        pass

    def shutdown(self, offset=103):
        shutdown_f_type = ctypes.CFUNCTYPE(ctypes.c_int)
        shutdown_f = shutdown_f_type(xinput._handle + offset)
        shutdown_f(self.device_number)
        return

class XInputController(Driver):

    def __init__(self, device_number, input_deadzone=0.01):
        self.controller = _XInputController(device_number, input_deadzone)
        return

    def set_axis_callback(self, f):
        try:
            self.controller.on_axis.disconnect()
        except TypeError:
            pass
        self.controller.on_axis.connect(f)
        return

    def set_button_callback(self, f):
        try:
            self.controller.on_button.disconnect()
        except TypeError:
            pass
        self.controller.on_button.connect(f)
        return

    def dispatch_events(self):
        self.controller.dispatch_events()
        return
