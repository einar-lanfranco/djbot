# -*- coding: utf-8 -*-
from botnet.aula.models import Tarea, Configuracion
from botnet import fabfile
import re
import subprocess
import os
import django_rq


def salida_computadora():
    archivo = open(fabfile.ARCHIVO, 'r')
    computadoras = {}
    patronIp = re.compile("\[([0-9.]*)\]")
    for each in archivo.readlines():
        if re.match(patronIp, each):
            ip = obtener_ip(patronIp, each)
            tipo, salida = obtener_salida(each)
            try:
                computadoras[ip].append(tipo + ':' + salida)
            except:
                computadoras[ip] = [tipo + ':' + salida]

    archivo.close()
    return computadoras


def obtener_salida(linea):
    salida = re.split("(: )", linea)
    try:
        tipo = re.search('run|out', salida[0]).group(0)
    except:
        tipo = 'out'
    return tipo, salida[2]


def borrar_archivo():
    subprocess.call(['rm', fabfile.ARCHIVO])


def obtener_ip(patron, linea):
    string = re.match(patron, linea).group(0)
    return re.sub("(\[)([0-9.]*)(\])", "\g<2>", string)


def escribir_ips(computadoras):
    compu = []
    for each in computadoras.values():
        compu.append(each['ip'])
    return compu


def ejecutar_tareas(tareas, computadoras):
    for unaTarea in tareas:
        instrucciones = Tarea.objects.filter(nombre=unaTarea)
        receta = instrucciones.values()[0]['instrucciones'].split('\n')
        if os.path.isfile(instrucciones.values()[0]['archivo']):
            if instrucciones.values()[0]['dividir_archivo']:
                cantidad = len(computadoras)
                secuencia_temporal = os.path.join(
                    Configuracion.objects.get(nombre="temporal").valor,
                    Configuracion.objects.get(nombre="secuencia").valor)
                fabfile.cortar(cantidad, instrucciones.values()[0]['archivo'],
                    secuencia_temporal)
                for each in range(0, cantidad):
                    print secuencia_temporal + str(each)
                    fabfile.enviar(secuencia_temporal + str(each).zfill(2),
                        computadoras[each])
            else:
                fabfile.enviar(instrucciones.values()[0]['archivo'],
                    computadoras)

        for each in receta:
            fabfile.ejecutar(each, computadoras)
