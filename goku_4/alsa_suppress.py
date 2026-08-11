"""ALSA warning suppression - must be imported first"""
import os
import sys

def suppress_alsa_warnings():
    try:
        import ctypes
        libasound = ctypes.CDLL("libasound.so.2")
        _alsa_handler_type = ctypes.CFUNCTYPE(
            None, ctypes.c_char_p, ctypes.c_int,
            ctypes.c_char_p, ctypes.c_int,
            ctypes.c_char_p, ctypes.c_int,
            ctypes.c_char_p
        )
        def _alsa_noop(filename, line, function, err, fmt, arg1, arg2):
            pass
        _alsa_handler = _alsa_handler_type(_alsa_noop)
        libasound.snd_lib_error_set_handler(_alsa_handler)
        sys._alsa_handler = _alsa_handler
    except Exception:
        pass

suppress_alsa_warnings()
