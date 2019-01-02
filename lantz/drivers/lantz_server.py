"""
    lantz.drivers.lantz_server.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This allows to access networked devices.abs

    WARNING: This is still experimental.  It uses pickle to serialize the object which is not secure in an untrusted environment.

    TODO: Implement DictFeat, Add Input check before executing, Fix autoquery when using autocomplete in ipython (maybe some caching is sufficient...)

    Author: Alexandre Bourassa
    Date: 05/24/2018
"""

import socketserver
import pickle
import codecs
from lantz import Driver, Q_, Feat, DictFeat, Action
import socket
import time
import sys
from importlib import import_module

def encode_data(data, protocol=None):
    data = pickle.dumps(data, protocol=protocol)
    if len(data) > 9999999999:
        raise OverflowError
    out = bytearray("{:010}".format(len(data)),'ascii')
    out.extend(data)
    return out

def msg_complete(data):
    if len(data)<10:
        return False
    length = int(data[:10])
    return len(data) == (length + 10)

def decode_data(data):
    if not msg_complete(data):
        raise Exception("Incomplete/Invalid data")
    length = data[:10]
    d = data[10:]
    obj = pickle.loads(d)

    # Special case to handle Quantity
    if repr(type(obj)) == "<class 'pint.quantity.build_quantity_class.<locals>.Quantity'>":
        obj = Q_(str(obj))
    return obj

def receive_all(recv_fun, timeout):
    start = time.time()
    data = bytearray()
    while (time.time()-start)<timeout:
        buf = recv_fun(1024)
        data.extend(buf)
        if msg_complete(data):
            return decode_data(data)
    raise TimeoutError


VALID_TYPES = {'Feat':Feat, 'Action':Action, 'DictFeat':DictFeat}
VALID_QUERY = ['SET', 'GET']
def build_query(property_type, property_name, query_type='GET',val=None, args=[], kwargs={}, key=None):
    if not property_type in VALID_TYPES:
        raise Exception('Invalid property type')
    if not query_type in VALID_QUERY:
        raise Exception('Invalid query type')
    if property_type == 'Feat':
        return {'property_type':property_type, 'property_name':property_name, 'query_type':query_type, 'val':val}
    if property_type == 'DictFeat':
        return {'property_type':property_type, 'property_name':property_name, 'query_type':query_type, 'val':val, 'args':args, 'kwargs':kwargs, 'key':key}
    if property_type == 'Action':
        return {'property_type':property_type, 'property_name':property_name, 'args':args, 'kwargs':kwargs}

def exec_query(dev, query):
    #TODO Add some input checks
    if query['property_type'] == 'Feat':
        if query['query_type'] == 'SET':
            try:
                setattr(dev, query['property_name'], query['val'])
                return build_reply()
            except:
                e = sys.exc_info()[0]
                print('error: \n{}'.format(e))
                return build_reply(error=e)
        elif query['query_type'] == 'GET':
            try:
                val = getattr(dev, query['property_name'])
                return build_reply(msg=val)
            except:
                e = sys.exc_info()[0]
                print('error: \n{}'.format(e))
                return build_reply(error=e)
    if query['property_type'] == 'Action':
        try:
            msg = getattr(dev, query['property_name'])(*query['args'], **query['kwargs'])
            return build_reply(msg=msg)
        except:
            e = sys.exc_info()[0]
            print('error: \n{}'.format(e))
            return build_reply(error=e)
    else:
        print('Unsupported')
        return build_reply(error='Unsupported')
    
def build_reply(error=None, msg=None):
    return {'error':error, 'msg':msg}
        


class Lantz_Server(socketserver.TCPServer):

    def __init__(self, host, port, device):
        class Lantz_Handler(socketserver.StreamRequestHandler):
            def handle(self):
                data = receive_all(self.request.recv, 1)
                print('received: {}'.format(data))
                reply = exec_query(device, data)
                print('reply: {}'.format(reply))
                self.request.sendall(encode_data(reply))

        super().__init__((host, port), Lantz_Handler)

# class Lantz_Base_Client(Driver):
#     def __init__(self, host, port, timeout=1):
#         self.host = host
#         self.port = port
#         self.timeout = timeout
                

#     def query(self, data):
#         #Initialize and send query
#         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         sock.connect((self.host, self.port))
#         sock.sendall(encode_data(data))

#         #Read back ans from the server
#         ans = receive_all(sock.recv, self.timeout)

#         sock.close()
#         return ans


class Device_Client():
    def __new__(cls, device_driver_class, host, port, timeout=1, allow_initialize_finalize=True):
        if type(device_driver_class) is str:
            class_name = device_driver_class.split('.')[-1]
            mod = import_module(device_driver_class.replace('.'+class_name, ''))
            device_driver_class = getattr(mod, class_name)
        
        class Device_Client_Instance(device_driver_class):
            __name__ = '_Device_Client.' + device_driver_class.__name__
            __qualname__ = 'Device_Client.' + device_driver_class.__name__
            _allow_initialize_finalize = allow_initialize_finalize
            def initialize(self):
                if self._allow_initialize_finalize:
                    self._initialize()
            def finalize(self):
                if self._allow_initialize_finalize:
                    self._finalize()

            def __init__(self, host, port, timeout=1):
                self.host = host
                self.port = port
                self.timeout = timeout
                

            def query(self, data):
                #Initialize and send query
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.host, self.port))
                sock.sendall(encode_data(data))

                #Read back ans from the server
                ans = receive_all(sock.recv, self.timeout)

                sock.close()
                return ans

        for feat_name, feat in device_driver_class._lantz_features.items():
            if isinstance(feat, Feat):
                def get_fun(_feat_name):
                    def f_(_self):
                        reply = _self.query(build_query('Feat', _feat_name, query_type='GET'))
                        if not reply['error'] is None:
                            raise reply['error']
                        else:
                            return reply['msg']
                    return f_

                def set_fun(_feat_name):
                    def f_(_self, val):
                        reply = _self.query(build_query('Feat', _feat_name, query_type='SET', val=val))
                        if not reply['error'] is None:
                            raise reply['error']
                        else:
                            return reply['msg']
                    return f_  
                setattr(Device_Client_Instance, feat_name, property(get_fun(feat_name), set_fun(feat_name)))
            #TODO implement DictFeat
            else:
                continue
        for action_name, action in device_driver_class._lantz_actions.items():
            def execute(_action_name):
                def f_(_self, *args, **kwargs):
                    reply = _self.query(build_query('Action', _action_name, args=args, kwargs=kwargs))
                    if not reply['error'] is None:
                        raise reply['error']
                    else:
                        return reply['msg']
                return f_
            if action_name in ['initialize', 'finalize']:
                setattr(Device_Client_Instance, '_'+action_name, execute(action_name))
            else:
                setattr(Device_Client_Instance, action_name, execute(action_name))

        
                    
        obj = Device_Client_Instance.__new__(Device_Client_Instance)
        obj.__init__(host, port, timeout=timeout)
        return obj

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    from lantz.drivers.stanford.sg396 import SG396

    sg = SG396('tcpip::192.168.1.108')

    server = Lantz_Server(HOST, PORT, sg)

    server.serve_forever()
