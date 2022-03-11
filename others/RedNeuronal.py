import torch
import torch.distributions.normal
import pickle
import Utilities as Ut
import os


class NN:
    def __init__(self):
        self.dtype = torch.float
        self.device = torch.device("cpu")

    def guardarModelo(self, number):
        if os.path.basename(os.getcwd()) != "Modelos":
            os.chdir('Modelos')
        with open(str('Modelo' + number), 'wb') as file:
            print()
            print('Guardado Modelo')
            pickle.dump(self, file)

    def cargarModelo(self, number):
        # print(os.getcwd())
        if os.path.basename(os.getcwd()) != "Modelos":
            os.chdir('Modelos')
            # print("Cambiando de directorio")
            # print(os.getcwd())
        try:
            with open(str('Modelo' + number), 'rb') as file:
                print('Cargando Modelo')
                try:
                    modelo = pickle.load(file)
                    self.__dict__.update(modelo.__dict__)
                except:
                    print("Error al cargar")
        except:
            print("Modelo previo no encontrado")


class NN_doscapas_unasalida_nograd(NN):
    def __init__(self, dimensionEntrada):
        super().__init__()
        self.dimensionEntrada = dimensionEntrada
        self.entradaModelo = [[]]
        self.capa1 = torch.empty(self.dimensionEntrada, self.dimensionEntrada, device=self.device,
                                 dtype=self.dtype).normal_(mean=0, std=1)
        self.capa2 = torch.empty(self.dimensionEntrada, 1, device=self.device, dtype=self.dtype).normal_(mean=0, std=1)
        self.salidaModelo = 0
        self.salida = torch.randn(1, device=self.device, dtype=self.dtype)

    def mutarCapas(self, coeficiente):
        mutacion1 = torch.empty(self.dimensionEntrada, self.dimensionEntrada).normal_(mean=0.5, std=1)
        mutacion1 = torch.where(mutacion1 < coeficiente, torch.tensor(1), torch.tensor(0))
        self.capa1 = torch.where(mutacion1 == 0, self.capa1,
                                 torch.empty(1, device=self.device, dtype=self.dtype).normal_(mean=0, std=1))
        mutacion2 = torch.empty(self.dimensionEntrada, 1).normal_(mean=0.5, std=1)
        mutacion2 = torch.where(mutacion2 < coeficiente, torch.tensor(1), torch.tensor(0))
        self.capa2 = torch.where(mutacion2 == 0, self.capa2,
                                 torch.empty(1, device=self.device, dtype=self.dtype).normal_(mean=0, std=1))

    def calculaSalida(self):
        entrada = torch.tensor(self.entradaModelo, device=torch.device("cpu"), dtype=torch.float)
        self.salida = entrada.mm(self.capa1).sigmoid().mm(self.capa2).item()

        if self.salida > 0.5:
            self.salidaModelo = 1
        else:
            self.salidaModelo = 0

    def mezcla(nn1, nn2, coeficiente):
        nn1.capa1 = (nn1.capa1 * coeficiente + nn2.capa1 * (1 - coeficiente))
        nn1.capa2 = (nn1.capa2 * coeficiente + nn2.capa2 * (1 - coeficiente))
        return nn1


class NN_doscapas_unasalida_grad(NN):
    def __init__(self, dimensionesEntrada):
        super().__init__()
        self.dimensionesEntrada = dimensionesEntrada
        self.entradaModelo = [[]]
        self.entrada = torch.randn(1, 1, device=self.device, dtype=self.dtype)
        self.salidaModelo = 0
        self.salida = torch.randn(1, device=self.device, dtype=self.dtype)
        self.salidaDeseada = torch.randn(1, device=self.device, dtype=self.dtype)

        self.capa1 = torch.randn(self.dimensionEntrada, self.dimensionEntrada, device=self.device,
                                 dtype=self.dtype, requires_grad=True)
        self.capa2 = torch.randn(self.dimensionEntrada, 1, device=self.device,
                                 dtype=self.dtype, requires_grad=True)

    def calculaSalida(self):

        self.entrada = torch.tensor(self.entradaModelo, device=self.device, dtype=torch.float)
        self.salida = self.entrada.mm(self.capa1).sigmoid().mm(self.capa2)

        if self.salida.item() > 0.5:
            self.salidaModelo = 1
        else:
            self.salidaModelo = 0

    def entrenar(self, salidaDeseada, coeficienteAprendizage):
        self.salidaDeseada = torch.tensor(salidaDeseada, device=self.device, dtype=self.dtype)
        coste = (self.salida - self.salidaDeseada).pow(2).sum()
        # print("coste")
        # print(coste)
        coste.backward()
        with torch.no_grad():
            self.capa1 -= coeficienteAprendizage * self.capa1.grad
            self.capa2 -= coeficienteAprendizage * self.capa2.grad
            self.capa1.grad.zero_()
            self.capa2.grad.zero_()
        return coste


class NN_trescapas_unasalida_grad(NN):
    def __init__(self, dimensionesEntrada):
        super().__init__()
        self.dimensionesEntrada = dimensionesEntrada
        self.entradaModelo = [[]]
        self.entrada = torch.randn(1, 1, device=self.device, dtype=self.dtype)
        self.salidaModelo = 0
        self.salida = torch.randn(1, device=self.device, dtype=self.dtype)
        self.salidaDeseada = torch.randn(1, device=self.device, dtype=self.dtype)

        self.capa1 = torch.randn(self.dimensionEntrada, self.dimensionEntrada, device=self.device,
                                 dtype=self.dtype, requires_grad=True)
        self.capa2 = torch.randn(self.dimensionEntrada, self.dimensionEntrada, device=self.device,
                                 dtype=self.dtype, requires_grad=True)
        self.capa3 = torch.randn(self.dimensionEntrada, 1, device=self.device,
                                 dtype=self.dtype, requires_grad=True)

    def calculaSalida(self):

        self.entrada = torch.tensor(self.entradaModelo, device=self.device, dtype=torch.float)
        self.salida = self.entrada.mm(self.capa1).sigmoid().mm(self.capa2).sigmoid().mm(self.capa3)

        if self.salida.item() > 0.5:
            self.salidaModelo = 1
        else:
            self.salidaModelo = 0

    def entrenar(self, salidaDeseada, coeficienteAprendizage):
        self.salidaDeseada = torch.tensor(salidaDeseada, device=self.device, dtype=self.dtype)
        coste = (self.salida - self.salidaDeseada).pow(2).sum()
        coste.backward()
        with torch.no_grad():
            self.capa1 -= coeficienteAprendizage * self.capa1.grad
            self.capa2 -= coeficienteAprendizage * self.capa2.grad
            self.capa1.grad.zero_()
            self.capa2.grad.zero_()
        return coste


class NN01_01(NN_doscapas_unasalida_nograd):

    def __init__(self, retenedoresEntrada, sistema):
        self.retenedoresEntrada = retenedoresEntrada
        dimensionEntrada = 0
        for i in self.retenedoresEntrada:
            dimensionEntrada += 2
            for j in range(0, len(sistema[i].salidas)):
                dimensionEntrada += 2
        super().__init__(dimensionEntrada)

    def __entradaDatos(self, i, sistema):
        self.entradaModelo[0].append(sistema[i].peticion)
        for j in range(0, len(sistema[i].salidas)):
            self.entradaModelo[0].append(sistema[i].avance[j])
        self.entradaModelo[0].append(sistema[i].bandejaEntrada.productType)
        for j in range(0, len(sistema[i].salidas)):
            self.entradaModelo[0].append(sistema[i].bandejasSalida[j].productType)

    def actualizarEntrada(self, sistema):
        self.entradaModelo[0] = []
        for i in self.retenedoresEntrada:
            self.__entradaDatos(i, sistema)

    def fitness(self, resultados, coeficienteProduccion, coeficienteColas):
        aux1 = sum(resultados.produccion) - 45
        aux2 = sum(resultados.tiempoPeticion)
        aux2 = 1 / (aux2 + 1)
        data = aux1 * coeficienteProduccion + aux2 * coeficienteColas
        return data


class NN01_02(NN_doscapas_unasalida_nograd):

    def __init__(self, colas):
        self.colas = colas
        self.dimensionEntrada = 2 * len(colas)
        super().__init__(self.dimensionEntrada)

    def __entradaDatos(self, i, sistema):
        ocupacion = [0, 0]
        total = 0
        for j in i:
            if sistema[j].bandejaEntrada.productType != -1:
                ocupacion[sistema[j].bandejaEntrada.productType] += 1
            total += 1
            for n in range(0, len(sistema[j].salidas)):
                if sistema[j].bandejasSalida[n].productType != -1:
                    ocupacion[sistema[j].bandejaEntrada.productType] += 1
                total += 1
        self.entradaModelo[0].append(ocupacion[0] / total)
        self.entradaModelo[0].append(ocupacion[1] / total)

    def actualizarEntrada(self, sistema):
        self.entradaModelo[0] = []
        for i in self.colas:
            self.__entradaDatos(i, sistema)

    def fitness(self, resultados, coeficienteProduccion, coeficienteColas):
        aux1 = sum(resultados.produccion) - 45
        aux2 = sum(resultados.tiempoPeticion)
        aux2 = 1 / (aux2 + 1)
        data = aux1 * coeficienteProduccion + aux2 * coeficienteColas
        return data

    def setEntrada(self, entrada):
        self.entradaModelo = entrada


class NN01_03(NN_doscapas_unasalida_grad):

    def __init__(self, colas):
        self.colas = colas
        self.dimensionEntrada = 2 * len(colas)
        super().__init__(self.dimensionEntrada)

    def __entradaDatos(self, i, sistema):
        ocupacion = [0, 0]
        total = 0
        for j in i:
            if sistema[j].bandejaEntrada.productType != -1:
                ocupacion[sistema[j].bandejaEntrada.productType] += 1
            total += 1
            for n in range(0, len(sistema[j].salidas)):
                if sistema[j].bandejasSalida[n].productType != -1:
                    ocupacion[sistema[j].bandejasSalida[n].productType] += 1
                total += 1
        self.entradaModelo[0].append(ocupacion[0] / total)
        self.entradaModelo[0].append(ocupacion[1] / total)

    def actualizarEntrada(self, sistema):
        self.entradaModelo[0] = []
        for i in self.colas:
            self.__entradaDatos(i, sistema)

    def setEntrada(self, entrada):
        self.entradaModelo = entrada

    def fitness(self, resultados, coeficienteProduccion, coeficienteColas):
        aux1 = sum(resultados.produccion) - 45
        aux2 = sum(resultados.tiempoPeticion)
        aux2 = 1 / (aux2 + 1)
        data = aux1 * coeficienteProduccion + aux2 * coeficienteColas
        return data


class NN02_01(NN_doscapas_unasalida_nograd):

    def __init__(self, retenedoresEntrada, sistema):
        self.retenedoresEntrada = retenedoresEntrada
        self.dimensionEntrada = 0
        for i in self.retenedoresEntrada:
            self.dimensionEntrada += 1
            for j in range(0, len(sistema[i].salidas)):
                self.dimensionEntrada += 1
        super().__init__(self.dimensionEntrada)

    def __entradaDatos(self, i, sistema):
        self.entradaModelo[0].append(sistema[i].bandejaEntrada.productType)
        for j in range(0, len(sistema[i].salidas)):
            self.entradaModelo[0].append(sistema[i].bandejasSalida[j].productType)

    def actualizarEntrada(self, sistema):
        self.entradaModelo[0] = []
        for i in self.retenedoresEntrada:
            self.__entradaDatos(i, sistema)


class NN02_01_01(NN02_01):

    def __init__(self, retenedoresEntrada, sistema):
        super().__init__(retenedoresEntrada, sistema)

    def fitness(self, resultados, coeficienteProduccion, coeficienteColas):
        # Ut.pNoEs("Modelo 1 Produccion: ")
        # Ut.pNoEs(resultados.produccion[0])
        aux1 = resultados.produccion[0]
        aux2 = sum(resultados.tiempoPeticion)
        aux2 = aux2 / ((aux2 ** 2 + 1) ** 0.5)
        data = aux1 * coeficienteProduccion + aux2 * coeficienteColas
        # Ut.pNoEs(' Fitness: ')
        # print(data)
        return data


class NN02_01_02(NN02_01):

    def __init__(self, retenedoresEntrada, sistema):
        super().__init__(retenedoresEntrada, sistema)

    def fitness(self, resultados, coeficienteProduccion, coeficienteColas):
        # Ut.pNoEs("Modelo 2 Produccion: ")
        # Ut.pNoEs(resultados.produccion[1])
        aux1 = resultados.produccion[1]
        aux2 = sum(resultados.tiempoPeticion)
        aux2 = aux2 / ((aux2 ** 2 + 1) ** 0.5)
        data = aux1 * coeficienteProduccion + aux2 * coeficienteColas
        # Ut.pNoEs(' Fitness: ')
        # print(data)
        return data


class NN02_02(NN_doscapas_unasalida_nograd):

    def __init__(self, colas):
        self.colas = colas
        self.dimensionEntrada = 2 * len(colas)
        super().__init__(self.dimensionEntrada)

    def __entradaDatos(self, i, sistema):
        ocupacion = [0, 0]
        total = 0
        for j in i:
            if sistema[j].bandejaEntrada.productType != -1:
                ocupacion[sistema[j].bandejaEntrada.productType] += 1
            total += 1
            for n in range(0, len(sistema[j].salidas)):
                if sistema[j].bandejasSalida[n].productType != -1:
                    ocupacion[sistema[j].bandejaEntrada.productType] += 1
                total += 1
        self.entradaModelo[0].append(ocupacion[0] / total)
        self.entradaModelo[0].append(ocupacion[1] / total)

    def actualizarEntrada(self, sistema):
        self.entradaModelo[0] = []
        for i in self.colas:
            self.__entradaDatos(i, sistema)


class NN02_02_01(NN02_02):

    def __init__(self, colas):
        super().__init__(colas)

    def fitness(self, resultados, coeficienteProduccion, coeficienteColas):
        # Ut.pNoEs("Modelo 1 Produccion: ")
        # Ut.pNoEs(resultados.produccion[0])
        aux1 = resultados.produccion[0]
        aux2 = sum(resultados.tiempoPeticion)
        aux2 = aux2 / ((aux2 ** 2 + 1) ** 0.5)
        data = aux1 * coeficienteProduccion + aux2 * coeficienteColas
        # Ut.pNoEs(' Fitness: ')
        # print(data)
        return data


class NN02_02_02(NN02_02):

    def __init__(self, colas):
        super().__init__(colas)

    def fitness(self, resultados, coeficienteProduccion, coeficienteColas):
        # Ut.pNoEs("Modelo 2 Produccion: ")
        # Ut.pNoEs(resultados.produccion[1])
        aux1 = resultados.produccion[1]
        aux2 = sum(resultados.tiempoPeticion)
        aux2 = aux2 / ((aux2 ** 2 + 1) ** 0.5)
        data = aux1 * coeficienteProduccion + aux2 * coeficienteColas
        # Ut.pNoEs(' Fitness: ')
        # print(data)
        return data


class NN02_03(NN_doscapas_unasalida_grad):

    def __init__(self, colas):
        self.colas = colas
        self.dimensionEntrada = 2 * len(colas)
        super().__init__(self.dimensionEntrada)

    def __entradaDatos(self, i, sistema):
        ocupacion = [0, 0]
        total = 0
        for j in i:
            if sistema[j].bandejaEntrada.productType != -1:
                ocupacion[sistema[j].bandejaEntrada.productType] += 1
            total += 1
            for n in range(0, len(sistema[j].salidas)):
                if sistema[j].bandejasSalida[n].productType != -1:
                    ocupacion[sistema[j].bandejasSalida[n].productType] += 1
                total += 1
        self.entradaModelo[0].append(ocupacion[0] / total)
        self.entradaModelo[0].append(ocupacion[1] / total)

    def actualizarEntrada(self, sistema):
        self.entradaModelo[0] = []
        for i in self.colas:
            self.__entradaDatos(i, sistema)

    def setEntrada(self, entrada):
        self.entradaModelo = entrada


class NN02_03_01(NN02_03):

    def __init__(self, colas):
        super().__init__(colas)

    def fitness(self, resultados, coeficienteProduccion, coeficienteColas):
        # Ut.pNoEs("Modelo 1 Produccion: ")
        # Ut.pNoEs(resultados.produccion[0])
        aux1 = resultados.produccion[0]
        aux2 = sum(resultados.tiempoPeticion)
        aux2 = aux2 / ((aux2 ** 2 + 1) ** 0.5)
        data = aux1 * coeficienteProduccion + aux2 * coeficienteColas
        # Ut.pNoEs(' Fitness: ')
        # print(data)
        return data


class NN02_03_02(NN02_03):

    def __init__(self, colas):
        super().__init__(colas)

    def fitness(self, resultados, coeficienteProduccion, coeficienteColas):
        # Ut.pNoEs("Modelo 2 Produccion: ")
        # Ut.pNoEs(resultados.produccion[1])
        aux1 = resultados.produccion[1]
        aux2 = sum(resultados.tiempoPeticion)
        aux2 = aux2 / ((aux2 ** 2 + 1) ** 0.5)
        data = aux1 * coeficienteProduccion + aux2 * coeficienteColas
        # Ut.pNoEs(' Fitness: ')
        # print(data)
        return data
