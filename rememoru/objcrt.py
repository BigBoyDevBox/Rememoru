"""Tiny Objective-C runtime bridge (just enough for the SLS bridged ops
and NSRunningApplication lookups)."""
import ctypes

objc = ctypes.CDLL("/usr/lib/libobjc.A.dylib")

objc_getClass = objc.objc_getClass
objc_getClass.restype = ctypes.c_void_p
objc_getClass.argtypes = [ctypes.c_char_p]

sel_registerName = objc.sel_registerName
sel_registerName.restype = ctypes.c_void_p
sel_registerName.argtypes = [ctypes.c_char_p]

_msgsend_addr = ctypes.cast(objc.objc_msgSend, ctypes.c_void_p).value

_sel_cache = {}


def sel(name):
    s = _sel_cache.get(name)
    if s is None:
        s = sel_registerName(name.encode("utf-8"))
        _sel_cache[name] = s
    return s


def get_class(name):
    return objc_getClass(name.encode("utf-8"))


def make_caller(restype, *argtypes):
    return ctypes.CFUNCTYPE(restype, ctypes.c_void_p, ctypes.c_void_p, *argtypes)(
        _msgsend_addr
    )


# Pre-built signatures we need
_send_id = make_caller(ctypes.c_void_p)                       # (id) -> id
_send_id_id_u64 = make_caller(                                # (id, u64) -> id
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint64
)
_send_id_i32 = make_caller(                                   # (i32) -> id
    ctypes.c_void_p, ctypes.c_int32
)
_send_bool_sel = make_caller(                                 # (SEL) -> BOOL
    ctypes.c_bool, ctypes.c_void_p
)


def alloc(cls):
    return _send_id(cls, sel("alloc"))


def init_with_windows_space_id(obj, windows_cfarray, space_id):
    return _send_id_id_u64(obj, sel("initWithWindows:spaceID:"), windows_cfarray, space_id)


def instances_respond_to(cls, selector_name):
    return _send_bool_sel(cls, sel("instancesRespondToSelector:"), sel(selector_name))


def running_app_with_pid(pid):
    cls = get_class("NSRunningApplication")
    if not cls:
        return None
    return _send_id_i32(cls, sel("runningApplicationWithProcessIdentifier:"), pid)


def bundle_identifier_of(nsrunningapp):
    if not nsrunningapp:
        return None
    return _send_id(nsrunningapp, sel("bundleIdentifier"))
