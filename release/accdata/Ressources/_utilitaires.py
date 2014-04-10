#!/usr/bin/env python
# encoding: utf-8

"""
utilitaires.py - Version tronquée pour ACC Data Analyzer
"""
import socket

############### Fonction getLocalIP #################
### Retourne l'addresse IP local de l'ordinateur  ###
#####################################################
def getLocalIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('google.ca', 9))
        client = s.getsockname()[0]
    except socket.error:
        client = "Unknown IP"
    finally:
        del s
    return client