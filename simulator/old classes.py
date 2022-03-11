import copy
import Utilities as Ut


class Tray:
    def __init__(self, trayId=-1, product=-1):
        self.id = id
        self.product = product

    def load_product(self, product):
        self.product = product

    def unload_product(self):
        product = self.product
        self.product = -1
        return product


class Product:
    def __init__(self, productId):
        self.productId = productId
        self.state = 0
        self.productType = 0


class Stopper:

    def __init__(self, stopperId: int, topology: list[list[int]], moveTime):
        self.stopperId = stopperId
        self.moveTime = moveTime
        self.moveTimer = []
        self.rest = True
        self.request = False
        self.move = [False] * len(topology[stopperId])
        self.stop = [False] * len(topology[stopperId])
        self.outputsIds = topology[stopperId]
        self.inputs = []
        self.sensor = False
        self.inputTray = -1
        self.outputTrays = []
        self.timer = 0
        self.inputTimer = 0
        self.processed = False

        for i in self.outputsIds:
            self.move += [False]
            self.stop += [False]
            self.moveTimer += [-1]
            self.outputTrays += [-1]

        for i in topology:
            if stopperId in topology[i]:
                self.inputs += [i]

    def lock(self, salida):
        self.stop[self.salidas.index(salida)] = True
        self.temporizador = -1

    def unlock(self, salida):
        self.stop[self.salidas.index(salida)] = False
        self.temporizador = -1

    def timed_lock(self, salida, tiempo):
        self.stop[self.salidas.index(salida)] = True
        self.temporizador = tiempo
        self.procesando = True

    def input(self, bandeja):
        if self.reposo:
            self.sensor = True
            self.bandejaEntrada = copy.deepcopy(bandeja)

    def estaAvanceA(self, destino):
        j = 0
        for i in self.salidas:
            if i == destino:
                if self.avance[j]: return True
            j += 1
        return False

    def estaOcupado(self, sistema):
        for i in self.entradas:
            if sistema[i].estaAvanceA(self.identificador): return True

        if self.reposo:
            return False
        else:
            return True

    def update(self, sistema, tiempo, log, resultado, actualizaEsperas):

        for i in range(0, len(self.salidas)):
            if self.stop[i]:
                if self.temporizador > 0:
                    self.temporizador -= 1
                elif self.temporizador == 0:
                    self.stop[i] = False
                    self.temporizador = -1
                    self.procesando = False

            if self.avance[i]:
                resultado.incrementarTiempo(self.identificador, 'avance')
                if not self.reposo and not self.peticion:
                    # if (tiempo - self.timerAvance[i]) >= 1:     # Hay que poner delay para los retenedores lentos
                    self.sensor = False
                    self.reposo = True

                if (tiempo - self.timerAvance[i]) > self.tiempoAvance:
                    sistema[self.salidas[i]].llegada(copy.deepcopy(self.bandejasSalida[i]))
                    self.bandejasSalida[i] = Tray()
                    self.avance[i] = False

            if self.peticion:
                if not self.stop[i] and not self.avance[i] and not sistema[self.salidas[i]].estaOcupado(sistema):
                    self.peticion = False
                    self.avance[i] = True
                    self.timerAvance[i] = tiempo
                    self.bandejasSalida[i] = copy.deepcopy(self.bandejaEntrada)
                    self.bandejaEntrada = Tray()

        if self.peticion:
            if actualizaEsperas:
                if not self.procesando:
                    resultado.incrementarTiempo(self.identificador, 'peticion')
                else:
                    resultado.incrementarTiempo(self.identificador, 'proceso')

        if self.reposo:
            if actualizaEsperas: resultado.incrementarTiempo(self.identificador, 'reposo')
            if self.sensor:
                self.tiempoEntrada = tiempo
                self.reposo = False
                self.peticion = True

    def influxData(self, measurement, time, logs):
        datos = {
            "measurement": measurement,
            "fields": {
                "estado": self.reposo * 2 ** 0 + self.peticion * 2 ** 1,
                "bandejaEntrada": str(self.bandejaEntrada.id) + ";" + str(self.bandejaEntrada.productType)
            },
            "tags": {
                "idRetenedor": self.identificador
            },
            "time": time
        }
        for i in range(0, len(self.salidas)):
            datos["fields"]["estado"] += int(self.avance[i]) * 2 ** (2 + i)
            datos["fields"]["bandejaSalida" + str(i)] = str(self.bandejasSalida[i].id) + ";" + str(
                self.bandejasSalida[i].productType)

        if logs: print(datos)
        return datos


class Output:
    def __init__(self, tiposDiferentes, cantidadRetenedores):
        self.produccion = []
        self.tiempoReposo = []
        self.tiempoPeticion = []
        self.tiempoAvance = []
        self.tiempoProceso = []

        for i in range(0, tiposDiferentes):
            self.produccion += [0]

        for i in range(0, cantidadRetenedores):
            self.tiempoReposo += [0]
            self.tiempoPeticion += [0]
            self.tiempoAvance += [0]
            self.tiempoProceso += [0]

    def producir(self, tipo):
        self.produccion[tipo] += 1

    def incrementarTiempo(self, retenedor, elemento):
        if elemento == 'reposo':
            self.tiempoReposo[retenedor] += 1
        if elemento == 'peticion':
            self.tiempoPeticion[retenedor] += 1
        if elemento == 'avance':
            self.tiempoAvance[retenedor] += 1
        if elemento == 'proceso':
            self.tiempoProceso[retenedor] += 1

    def print(self):
        print('')
        Ut.pNoEs('Produccion: ')
        print(self.produccion)
        Ut.pNoEs('Reposo: ')
        print(self.tiempoReposo)
        Ut.pNoEs('Peticion: ')
        print(self.tiempoPeticion)
        Ut.pNoEs('Avance: ')
        print(self.tiempoAvance)
        Ut.pNoEs('Proceso: ')
        print(self.tiempoProceso)

    def exportar(self):
        return [self.produccion, self.tiempoReposo, self.tiempoProceso, self.tiempoPeticion, self.tiempoAvance]
