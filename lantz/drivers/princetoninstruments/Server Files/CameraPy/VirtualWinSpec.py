import winspec as ws
import socket
import numpy as np
import pickle
import json
import time

print "Winspec is imported"
socket.setdefaulttimeout(None)

def initiate_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    host = socket.gethostname()
    IP = socket.gethostbyname(host)
    port = 12345
    s.settimeout(300)
    print "The IP address is ", IP
    print "The SOCKET number is ", port
    print "Waiting for connection ..."
    s.bind((host, port))
    s.listen(5)
    c, addr = s.accept()
    print "Connection Established with ", addr
    s.settimeout(None)
    return c


no_arg_functions = {
    "get exposure time": ws.get_exposure_time,
    "get grating": ws.get_grating,
    "get ngrating": ws.get_ngratings,
    "get current turret": ws.get_current_turret,
    "get temperature": ws.get_temperature,
    "get target temperature": ws.get_target_temperature,
    "get wavelength": ws.get_wavelength
    }

one_arg_send_functions = {
    "set exposure time": ws.set_exposure_time,
    "set grating": ws.set_grating,
    "set target temperature": ws.set_target_temperature,
    "set wavelength": ws.set_wavelength
    }

one_arg_get_functions = {
    "get grating grooves": ws.get_grating_grooves,
    "get grating name": ws.get_grating_name
    }

def get_spectrum():
    spectrum = ws.get_spectrum()
    return json.dumps(spectrum.tolist())

def get_wavelengths():
    wavelengths = ws.get_wavelengths()
    return json.dumps(wavelengths)

def one_arg_function(command):
    split_list = command.split()
    val = float(split_list[-1])
    function = " ".join(split_list[0:-1])
    res = one_arg_functions[function](val)
    return str(res)

def parse_one_arg_functions(command):
    split_list = command.split()
    val = split_list[-1]
    function = " ".join(split_list[0:-1])
    return function, val    

def no_arg_function(command):
    return str(no_arg_functions[command]())

def recieve_and_send(command):
    if command == "get spectrum":
        return get_spectrum()
    elif command == "get wavelengths":
        return get_wavelengths()
    else:
        if command in no_arg_functions.keys():
            return no_arg_function(command)
        else:
            command, val = parse_one_arg_functions(command)
            if command in one_arg_send_functions.keys():
                one_arg_send_functions[command](float(val))
                return "OK"
            elif command in one_arg_get_functions.keys():
                return str(one_arg_get_functions[command](int(val)))
            else:
                return "Unidennd"

def establish_communication():
    c = initiate_server()
    try:
        socketerror1035count = 0
        while True:
            try:
                command = c.recv(1024)
                #print command
                if not command: break
                if command == "close":
                    break
                to_be_sent = recieve_and_send(command) +"\r\n"
                #print to_be_sent
                c.send(to_be_sent)
            except socket.error as e:
                if e[0] == 10035 and socketerror1035count < 5:
                    socketerror1035count = socketerror1035count  +1
                    time.sleep(1)
    finally:
        c.close()

if __name__ == "__main__":
    while True:
        establish_communication()
        time.sleep(0.5)
