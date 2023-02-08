######## Importacion librerias ########
import time
from influxdb import InfluxDBClient
from sim.objects import tray
import copy
import tkinter
import Utilities as Ut


class SimuladorInteractivo:

    # Funciones de la app
    def entradaProductoTipo1(self):  # De momento se ignora el id de la bandeja
        self.modeloPlanta[0].llegada(tray.Tray(self.indiceBandeja, 0))
        self.indiceBandeja += 1

    def entradaProductoTipo2(self):  # De momento se ignora el id de la bandeja
        self.modeloPlanta[0].llegada(tray.Tray(self.indiceBandeja, 1))
        self.indiceBandeja += 1

    def paradaSimulacion(self):
        self.paroSimulacion = True

    def __init__(self, logs):
        ######## Instancion de elementos ########

        # Info base de datos a utilizar
        self.baseDeDatos = 'Pruebas'
        self.measurement = 'Sim'

        # Variables de simulacion
        self.tiempo = 0
        self.paso = 0

        # Parametros de simualacion
        self.desplazamientoTiempoInicio = 240 * 10 ** 9
        self.intervaloTiempo = 1 * 10 ** 9
        self.tiempoReal = True
        self.almacenajeDatos = True
        self.paroSimulacion = False
        self.actualizarResultados = True
        self.logsActivos = logs
        self.logsNN = True

        # Objetos de la simulacion
        self.indice = [*range(34)]
        self.topologia = [[1], [2], [3], [4], [5, 9], [6], [7], [8], [13], [10], [11], [12], [8], [14], [15], [16, 25],
                          [17], [18], [19, 29], [20], [21], [22], [23], [6, 24], [2], [26], [27], [28], [30], [30],
                          [31], [32], [33], [20]]
        self.tiempomodeloPlanta = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                                   2, 2, 2, 2, 2, 2]
        self.modeloPlanta = []
        self.modeloPlantaAnterior = []

        # Inicializacion objetos simulacion
        for i in self.indice:
            self.modeloPlanta += [tray.Stopper(self.indice[i], self.topologia, self.tiempomodeloPlanta[i], len(self.topologia))]

        # Iniciacion almacenamiento datos a guardar
        self.dataSend = []

        # Inicializacion almacenamiento resultados
        self.resultado = tray.Output(2, 34)

        # Instancia cliente influx y borrado de datos anteriores
        if self.almacenajeDatos: self.client = InfluxDBClient('127.0.0.1', 8086, '', '', self.baseDeDatos)
        if self.almacenajeDatos: self.client.drop_measurement(self.measurement)

        self.productoAnterior = 1
        self.indiceBandeja = 1
        ######## Aplicacion de control ########
        self.app = tkinter.Tk()
        self.app.title("Sim Controller")
        self.etiqueta1 = tkinter.Label(self.app, text="Entrada -> ")
        self.etiqueta1.grid(column=0, row=0)
        self.app.geometry('350x250')
        self.boton1 = tkinter.Button(self.app, text="Producto 1", command=self.entradaProductoTipo1)
        self.boton1.grid(column=1, row=0)
        self.boton2 = tkinter.Button(self.app, text="Producto 2", command=self.entradaProductoTipo2)
        self.boton2.grid(column=2, row=0)
        self.boton3 = tkinter.Button(self.app, text="Stop", command=self.paradaSimulacion)
        self.boton3.grid(column=3, row=0)

    ######## Funciones ########
    # Funciones de control del sistema
    def controlR3(self):
        # Comprobamos el tipo de producto actual
        if self.modeloPlanta[3].peticion:
            if self.modeloPlanta[3].bandejaEntrada.status and not self.modeloPlanta[3].stop[0]:
                self.modeloPlanta[3].bloquearTiempo(4, 10)
                if self.modeloPlanta[3].bandejaEntrada.productType == 0:
                    self.resultado.producir(0)
                else:
                    self.resultado.producir(1)
                self.modeloPlanta[3].bandejaEntrada.vaciar()

    def controlR4(self):
        if self.modeloPlanta[4].peticion:
            self.modeloPlanta[4].bloquear(5)
            self.modeloPlanta[4].bloquear(9)
            if self.modeloPlanta[4].bandejaEntrada.materiaPrima:
                self.modeloPlanta[4].desbloquear(5)
            else:
                self.modeloPlanta[4].desbloquear(9)

    def controlR10(self):
        if self.modeloPlanta[10].peticion:
            if not self.modeloPlanta[10].bandejaEntrada.materiaPrima and not self.modeloPlanta[10].stop[0]:
                self.modeloPlanta[10].bloquearTiempo(11, 10)
                if self.productoAnterior == 0:
                    self.modeloPlanta[10].bandejaEntrada.nuevoProducto(1)
                    self.productoAnterior = 1
                else:
                    self.modeloPlanta[10].bandejaEntrada.nuevoProducto(0)
                    self.productoAnterior = 0
                self.modeloPlanta[10].bandejaEntrada.cargarMateriaPrima()

    def controlR15(self):
        if self.modeloPlanta[15].peticion:
            self.modeloPlanta[15].bloquear(16)
            self.modeloPlanta[15].bloquear(25)
            if self.modeloPlanta[15].bandejaEntrada.productType == 0:
                self.modeloPlanta[15].desbloquear(25)
            else:
                self.modeloPlanta[15].desbloquear(16)

    def controlR18(self):
        if self.modeloPlanta[18].peticion:
            self.modeloPlanta[18].bloquear(19)
            self.modeloPlanta[18].bloquear(29)
            if self.modeloPlanta[18].bandejaEntrada.productType == 1 and not self.modeloPlanta[18].bandejaEntrada.status and self.modeloPlanta[18].bandejaEntrada.materiaPrima:
                self.modeloPlanta[18].desbloquear(29)
            else:
                self.modeloPlanta[18].desbloquear(19)

    def controlR23(self):
        if self.modeloPlanta[23].peticion:
            self.modeloPlanta[23].bloquear(24)
            self.modeloPlanta[23].bloquear(6)
            if self.modeloPlanta[23].bandejaEntrada.status or not self.modeloPlanta[23].bandejaEntrada.materiaPrima:
                self.modeloPlanta[23].desbloquear(24)
            else:
                self.modeloPlanta[23].desbloquear(6)

    def controlR27(self):
        if self.modeloPlanta[27].peticion:
            if not self.modeloPlanta[27].stop[0] and self.modeloPlanta[27].bandejaEntrada.productType == 0 and self.modeloPlanta[27].bandejaEntrada.materiaPrima and not self.modeloPlanta[
                27].bandejaEntrada.status:
                self.modeloPlanta[27].bloquearTiempo(28, 10)
                self.modeloPlanta[27].bandejaEntrada.finalizar()

    def controlR31(self):
        if self.modeloPlanta[31].peticion:
            if not self.modeloPlanta[31].stop[0] and self.modeloPlanta[31].bandejaEntrada.productType == 1 and self.modeloPlanta[31].bandejaEntrada.materiaPrima and not self.modeloPlanta[
                31].bandejaEntrada.status:
                self.modeloPlanta[31].bloquearTiempo(32, 10)
                self.modeloPlanta[31].bandejaEntrada.finalizar()

    # Funcion de carga de datos en influx
    def cargarDatos(self, i):
        if self.almacenajeDatos:
            if self.tiempoReal:
                temporal0 = self.client.write_points([self.modeloPlanta[i].influxData(self.measurement, self.tiempo, self.logsActivos)])
                if self.logsActivos: print(temporal0)
            else:
                self.dataSend.append(self.modeloPlanta[i].influxData(self.measurement, self.tiempo, self.logsActivos))

    ######## Simulacion del sistema ########
    def simular(self, salidaResultado, totalSimulacion):
        i = 0

        # Inicializacion temporal
        if self.tiempoReal:
            self.tiempo = time.time_ns()
        else:
            self.tiempo = time.time_ns() - self.desplazamientoTiempoInicio

        # Carga datos iniciales
        if self.almacenajeDatos:
            for i in self.indice:
                self.cargarDatos(i)

        # Simulacion
        self.paso = 0
        while (self.paso < totalSimulacion or self.tiempoReal) and not self.paroSimulacion:

            # Entrada de productos
            if not self.tiempoReal:
                if self.paso % 20 == 0 and self.paso < 80 and self.paso > 5:
                    self.modeloPlanta[0].llegada(tray.Tray(self.paso, -1))

            if self.tiempoReal: self.app.update()

            # Copia del estado anterior
            self.modeloPlantaAnterior = copy.deepcopy(self.modeloPlanta)

            # Actualización de self.modeloPlanta en varios pasos
            for n in range(0, 3):
                if n == 2:
                    self.actualizarResultados = True
                else:
                    self.actualizarResultados = False
                # Control de las bandejas
                self.controlR3()
                self.controlR4()
                self.controlR10()
                self.controlR15()
                self.controlR18()
                self.controlR23()
                self.controlR27()
                self.controlR31()

                if self.logsActivos: print("")
                if self.logsActivos: Ut.pNoEs(str(self.paso) + "." + str(n))

                for i in self.indice:
                    self.modeloPlanta[i].update(self.modeloPlanta, self.paso, self.logsActivos, self.resultado, self.actualizarResultados)
                    if n == 2:
                        if self.modeloPlantaAnterior[i] != self.modeloPlanta[i]:
                            if self.almacenajeDatos: self.cargarDatos(i)

            # Calculo del tiempo siguiente step
            if self.tiempoReal:
                time.sleep(self.intervaloTiempo / (10 ** 9.5))
                self.tiempo = time.time_ns()
            else:
                self.tiempo += self.paso * self.intervaloTiempo

            self.paso += 1

        if self.almacenajeDatos:
            for i in self.indice:
                self.cargarDatos(i)

        temporal0 = False
        if self.almacenajeDatos and not self.tiempoReal:
            temporal0 = self.client.write_points(self.dataSend)
            if self.logsActivos: print(temporal0)

        if salidaResultado: return self.resultado


class Simulador01:

    def __init__(self, logs):
        ######## Instancion de elementos ########

        # Info base de datos a utilizar
        self.baseDeDatos = 'Pruebas'
        self.measurement = 'Sim'

        # Variables de simulacion
        self.tiempo = 0
        self.paso = 0

        # Parametros de simualacion
        self.desplazamientoTiempoInicio = 240 * 10 ** 9
        self.intervaloTiempo = 1 * 10 ** 9
        self.tiempoReal = False
        self.almacenajeDatos = False
        self.paroSimulacion = False
        self.actualizarResultados = False
        self.logsActivos = logs
        self.logsNN = True
        self.cargaAnterior = 0

        # Objetos de la simulacion
        self.indice = [*range(34)]
        self.topologia = [[1], [2], [3], [4], [5, 9], [6], [7], [8], [13], [10], [11], [12], [8], [14], [15], [16, 25],
                          [17], [18], [19, 29], [20], [21], [22], [23], [6, 24], [2], [26], [27], [28], [30], [30],
                          [31], [32], [33], [20]]
        self.tiempomodeloPlanta = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                                   1, 1, 1, 1, 1, 1]
        self.modeloPlanta = []
        self.modeloPlantaAnterior = []
        self.bandejasTotales = 0

        # Inicializacion objetos simulacion
        for i in self.indice:
            self.modeloPlanta += [tray.Stopper(self.indice[i], self.topologia, self.tiempomodeloPlanta[i], len(self.topologia))]

        # Inicializacion almacenamiento resultados
        self.resultado = tray.Output(2, 34)

    ######## Funciones ########
    # Funciones de control del sistema
    def controlR1(self):
        # Comprobamos el tipo de producto actual
        if self.modeloPlanta[1].peticion:
            if self.modeloPlanta[24].peticion:
                self.modeloPlanta[1].bloquear(2)
            else:
                self.modeloPlanta[1].desbloquear(2)

    def controlR3(self):
        # Comprobamos el tipo de producto actual
        if self.modeloPlanta[3].peticion:
            if self.modeloPlanta[3].bandejaEntrada.status and not self.modeloPlanta[3].stop[0]:
                self.modeloPlanta[3].bloquearTiempo(4, 10)
                if self.modeloPlanta[3].bandejaEntrada.productType == 0:
                    self.resultado.producir(0)
                else:
                    self.resultado.producir(1)
                self.modeloPlanta[3].bandejaEntrada.vaciar()

    def controlR4(self):
        if self.modeloPlanta[4].peticion:
            self.modeloPlanta[4].bloquear(5)
            self.modeloPlanta[4].bloquear(9)
            if self.modeloPlanta[4].bandejaEntrada.materiaPrima:
                self.modeloPlanta[4].desbloquear(5)
            else:
                self.modeloPlanta[4].desbloquear(9)

    def controlR10(self, NN):
        if self.modeloPlanta[10].peticion:
            if not self.modeloPlanta[10].bandejaEntrada.materiaPrima and not self.modeloPlanta[10].stop[0]:
                NN.actualizarEntrada(self.modeloPlanta)
                NN.calculaSalida()
                self.modeloPlanta[10].bloquearTiempo(11, 10)
                # if self.logsNN: print(NN.salidaModelo)
                # if self.cargaAnterior == 0: self.cargaAnterior = 1
                # else: self.cargaAnterior = 0
                self.modeloPlanta[10].bandejaEntrada.nuevoProducto(NN.salidaModelo)
                # self.modeloPlanta[10].bandejaEntrada.nuevoProducto(self.cargaAnterior)
                self.modeloPlanta[10].bandejaEntrada.cargarMateriaPrima()

    def controlR15(self):
        if self.modeloPlanta[15].peticion:
            self.modeloPlanta[15].bloquear(16)
            self.modeloPlanta[15].bloquear(25)
            if self.modeloPlanta[15].bandejaEntrada.productType == 0:
                self.modeloPlanta[15].desbloquear(25)
            else:
                self.modeloPlanta[15].desbloquear(16)

    def controlR18(self):
        if self.modeloPlanta[18].peticion:
            self.modeloPlanta[18].bloquear(19)
            self.modeloPlanta[18].bloquear(29)
            if self.modeloPlanta[18].bandejaEntrada.productType == 1 and not self.modeloPlanta[18].bandejaEntrada.status and self.modeloPlanta[18].bandejaEntrada.materiaPrima:
                self.modeloPlanta[18].desbloquear(29)
            else:
                self.modeloPlanta[18].desbloquear(19)

    def controlR23(self):
        if self.modeloPlanta[23].peticion:
            self.modeloPlanta[23].bloquear(24)
            self.modeloPlanta[23].bloquear(6)
            if self.modeloPlanta[23].bandejaEntrada.status or not self.modeloPlanta[23].bandejaEntrada.materiaPrima:
                self.modeloPlanta[23].desbloquear(24)
            else:
                self.modeloPlanta[23].desbloquear(6)

    def controlR28(self):
        if self.modeloPlanta[28].peticion:
            if not self.modeloPlanta[28].stop[0] and self.modeloPlanta[28].bandejaEntrada.productType == 0 and \
                    self.modeloPlanta[28].bandejaEntrada.materiaPrima and not self.modeloPlanta[
                28].bandejaEntrada.status:
                self.modeloPlanta[28].bloquearTiempo(30, 100)
                self.modeloPlanta[28].bandejaEntrada.finalizar()

    def controlR31(self):
        if self.modeloPlanta[31].peticion:
            if not self.modeloPlanta[31].stop[0] and self.modeloPlanta[31].bandejaEntrada.productType == 1 and self.modeloPlanta[31].bandejaEntrada.materiaPrima and not self.modeloPlanta[
                31].bandejaEntrada.status:
                self.modeloPlanta[31].bloquearTiempo(32, 100)
                self.modeloPlanta[31].bandejaEntrada.finalizar()

    ######## Simulacion del sistema ########
    def simular(self, NN, totalSimulacion):
        i = 0
        self.paso = 0
        while self.paso < totalSimulacion:
            if self.modeloPlanta[0].reposo and self.bandejasTotales < 100:
                self.modeloPlanta[0].llegada(tray.Tray(self.paso, -1))
                self.bandejasTotales += 1

            # Actualización de self.modeloPlanta en varios pasos
            for n in range(0, 3):

                if n == 2:
                    self.actualizarResultados = True
                else:
                    self.actualizarResultados = False

                # Control de las bandejas
                self.controlR1()
                self.controlR3()
                self.controlR4()
                self.controlR10(NN)
                self.controlR15()
                self.controlR18()
                self.controlR23()
                self.controlR28()
                self.controlR31()

                for i in self.indice:
                    self.modeloPlanta[i].update(self.modeloPlanta, self.paso, self.logsActivos, self.resultado, self.actualizarResultados)

            self.paso += 1

        return self.resultado


class Simulador02:

    def __init__(self, logs):
        ######## Instancion de elementos ########

        # Info base de datos a utilizar
        self.baseDeDatos = 'Pruebas'
        self.measurement = 'Sim'

        # Variables de simulacion
        self.tiempo = 0
        self.paso = 0

        # Parametros de simualacion
        self.desplazamientoTiempoInicio = 240 * 10 ** 9
        self.intervaloTiempo = 1 * 10 ** 9
        self.tiempoReal = False
        self.almacenajeDatos = False
        self.paroSimulacion = False
        self.actualizarResultados = False
        self.logsActivos = logs
        self.logsNN = True
        self.cargaAnterior = 0

        # Objetos de la simulacion
        self.indice = [*range(34)]
        self.topologia = [[1], [2], [3], [4], [5, 9], [6], [7], [8], [13], [10], [11], [12], [8], [14], [15], [16, 25],
                          [17], [18], [19, 29], [20], [21], [22], [23], [6, 24], [2], [26], [27], [28], [30], [30], [31], [32], [33], [20]]
        self.tiempomodeloPlanta = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                                   1, 1, 1, 1, 1, 1]
        self.modeloPlanta = []
        self.modeloPlantaAnterior = []
        self.bandejasTotales = 0

        # Inicializacion objetos simulacion
        for i in self.indice:
            self.modeloPlanta += [tray.Stopper(self.indice[i], self.topologia, self.tiempomodeloPlanta[i], len(self.topologia))]

        # Inicializacion almacenamiento resultados
        self.resultado = tray.Output(2, 34)

    ######## Funciones ########
    # Funciones de control del sistema

    def controlR1(self):
        # Comprobamos el tipo de producto actual
        if self.modeloPlanta[1].peticion:
            if self.modeloPlanta[24].peticion:
                self.modeloPlanta[1].bloquear(2)
            else:
                self.modeloPlanta[1].desbloquear(2)

    def controlR3(self):
        # Comprobamos el tipo de producto actual
        if self.modeloPlanta[3].peticion:
            if self.modeloPlanta[3].bandejaEntrada.status and not self.modeloPlanta[3].stop[0]:
                self.modeloPlanta[3].bloquearTiempo(4, 10)
                if self.modeloPlanta[3].bandejaEntrada.productType == 0:
                    self.resultado.producir(0)
                else:
                    self.resultado.producir(1)
                self.modeloPlanta[3].bandejaEntrada.vaciar()

    def controlR4(self):
        if self.modeloPlanta[4].peticion:
            self.modeloPlanta[4].bloquear(5)
            self.modeloPlanta[4].bloquear(9)
            if self.modeloPlanta[4].bandejaEntrada.materiaPrima:
                self.modeloPlanta[4].desbloquear(5)
            else:
                self.modeloPlanta[4].desbloquear(9)

    def controlR10(self):
        if self.modeloPlanta[10].peticion:
            if not self.modeloPlanta[10].bandejaEntrada.materiaPrima and not self.modeloPlanta[10].stop[0]:
                self.modeloPlanta[10].bloquearTiempo(11, 10)
                if self.cargaAnterior == 0:
                    self.cargaAnterior = 1
                else:
                    self.cargaAnterior = 0
                self.modeloPlanta[10].bandejaEntrada.nuevoProducto(self.cargaAnterior)
                self.modeloPlanta[10].bandejaEntrada.cargarMateriaPrima()

    def controlR15(self, NN):
        if self.modeloPlanta[15].peticion:
            self.modeloPlanta[15].bloquear(16)
            self.modeloPlanta[15].bloquear(25)
            NN.actualizarEntrada(self.modeloPlanta)
            NN.calculaSalida()
            if NN.salidaModelo == 1 and not self.modeloPlanta[15].bandejaEntrada.status and self.modeloPlanta[15].bandejaEntrada.materiaPrima and self.modeloPlanta[15].bandejaEntrada.productType == 0:
                self.modeloPlanta[15].desbloquear(25)
            else:
                self.modeloPlanta[15].desbloquear(16)
            # if self.modeloPlanta[15].bandejaEntrada.tipo == 0 and not self.modeloPlanta[15].bandejaEntrada.finalizado and self.modeloPlanta[15].bandejaEntrada.materiaPrima:
            #     self.modeloPlanta[15].desbloquear(25)
            # else:
            #     self.modeloPlanta[15].desbloquear(16)

    def controlR18(self, NN):
        if self.modeloPlanta[18].peticion:
            self.modeloPlanta[18].bloquear(19)
            self.modeloPlanta[18].bloquear(29)
            NN.actualizarEntrada(self.modeloPlanta)
            NN.calculaSalida()
            if NN.salidaModelo == 1 and not self.modeloPlanta[18].bandejaEntrada.status and self.modeloPlanta[18].bandejaEntrada.materiaPrima and self.modeloPlanta[15].bandejaEntrada.productType == 1:
                self.modeloPlanta[18].desbloquear(29)
            else:
                self.modeloPlanta[18].desbloquear(19)
            # if self.modeloPlanta[18].bandejaEntrada.tipo == 1 and not self.modeloPlanta[18].bandejaEntrada.finalizado and self.modeloPlanta[18].bandejaEntrada.materiaPrima:
            #     self.modeloPlanta[18].desbloquear(29)
            # else:
            #     self.modeloPlanta[18].desbloquear(19)

    def controlR23(self):
        if self.modeloPlanta[23].peticion:
            self.modeloPlanta[23].bloquear(24)
            self.modeloPlanta[23].bloquear(6)
            if self.modeloPlanta[23].bandejaEntrada.status or not self.modeloPlanta[23].bandejaEntrada.materiaPrima:
                self.modeloPlanta[23].desbloquear(24)
            else:
                self.modeloPlanta[23].desbloquear(6)

    def controlR28(self):
        if self.modeloPlanta[28].peticion:
            if not self.modeloPlanta[28].stop[0] and self.modeloPlanta[28].bandejaEntrada.productType == 0 and \
                    self.modeloPlanta[28].bandejaEntrada.materiaPrima and not self.modeloPlanta[
                28].bandejaEntrada.status:
                self.modeloPlanta[28].bloquearTiempo(30, 100)
                self.modeloPlanta[28].bandejaEntrada.finalizar()

    def controlR31(self):
        if self.modeloPlanta[31].peticion:
            if not self.modeloPlanta[31].stop[0] and self.modeloPlanta[31].bandejaEntrada.productType == 1 and self.modeloPlanta[31].bandejaEntrada.materiaPrima and not self.modeloPlanta[
                31].bandejaEntrada.status:
                self.modeloPlanta[31].bloquearTiempo(32, 100)
                self.modeloPlanta[31].bandejaEntrada.finalizar()

    ######## Simulacion del sistema ########
    def simular(self, NN1, NN2, totalSimulacion):
        i = 0
        self.paso = 0
        while self.paso < totalSimulacion:
            if self.modeloPlanta[0].reposo and self.bandejasTotales < 100:
                self.modeloPlanta[0].llegada(tray.Tray(self.paso, -1))
                self.bandejasTotales += 1

            # Actualización de self.modeloPlanta en varios pasos
            for n in range(0, 3):

                if n == 2:
                    self.actualizarResultados = True
                else:
                    self.actualizarResultados = False

                # Control de las bandejas
                self.controlR1()
                self.controlR3()
                self.controlR4()
                self.controlR10()
                self.controlR15(NN1)
                self.controlR18(NN2)
                self.controlR23()
                self.controlR28()
                self.controlR31()

                for i in self.indice:
                    self.modeloPlanta[i].update(self.modeloPlanta, self.paso, self.logsActivos, self.resultado, self.actualizarResultados)

            self.paso += 1

        return self.resultado
