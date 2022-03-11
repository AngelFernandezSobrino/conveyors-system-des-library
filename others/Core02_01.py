import Sim
import copy
import RedNeuronal
import Utilities as Ut

# Modelo02_01 control de bifurcaciones - Genetico
individuosPorGeneracion = 15
generaciones = 40
tiempoSimulacion = 2000
individuosSeleccion = 2
coeficienteProduccion = 0.8
coeficienteColas = 0.2
coeficienteMutacion = 0.15
seleccion = [[0, 0], [0, 0]]

NN1 = []
NN2 = []
resultados = []
fitness = []

simulador = Sim.Simulador02(logs=True)

retenedoresEntrada01 = [6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
                        20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33]
retenedoresEntrada02 = [6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
                        20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33]

for i in range(0, individuosPorGeneracion):
    NN1.append(RedNeuronal.NN02_01_01(retenedoresEntrada01, simulador.modeloPlanta))
for i in range(0, individuosPorGeneracion):
    NN2.append(RedNeuronal.NN02_01_02(retenedoresEntrada02, simulador.modeloPlanta))

for individuo in range(0, len(NN1)):
    NN1[individuo].cargarModelo('02_01_01_prueba')

for individuo in range(0, len(NN2)):
    NN2[individuo].cargarModelo('02_01_02_prueba')

for generacion in range(0, generaciones):
    seleccion = [[0, 0], [0, 0]]
    print()
    Ut.pNoEs('Generacion ')
    print(generacion)
    resultados.append([])
    fitness.append([])
    for individuo in range(0, len(NN1)):
        simulador = Sim.Simulador02(logs=True)
        resultados[generacion].append(simulador.simular(NN1[individuo], NN2[individuo], tiempoSimulacion))

        fitness[generacion].append(
            [NN1[individuo].fitness(resultados[generacion][-1], coeficienteProduccion, coeficienteColas),
             NN2[individuo].fitness(resultados[generacion][-1], coeficienteProduccion, coeficienteColas)])
        Ut.pNoEs("Produccion: ")
        Ut.pNoEs(resultados[-1][0].produccion[0])
        Ut.pNoEs(" : ")
        print(resultados[-1][0].produccion[1])
    indice = 0
    for fitnessIndividuo in fitness[generacion]:
        if fitnessIndividuo[0] > fitness[generacion][seleccion[0][0]][0]:
            seleccion[0][1] = copy.deepcopy(seleccion[0][0])
            seleccion[0][0] = copy.copy(indice)
        elif fitnessIndividuo[0] > fitness[generacion][seleccion[0][1]][0]:
            seleccion[0][1] = copy.copy(indice)
        if fitnessIndividuo[1] > fitness[generacion][seleccion[1][0]][1]:
            seleccion[1][1] = copy.deepcopy(seleccion[0][0])
            seleccion[1][0] = copy.copy(indice)
        elif fitnessIndividuo[1] > fitness[generacion][seleccion[1][1]][1]:
            seleccion[1][1] = copy.copy(indice)
        indice += 1

    seleccion[0][0] = copy.deepcopy(NN1[seleccion[0][0]])
    seleccion[0][1] = copy.deepcopy(NN1[seleccion[0][1]])
    seleccion[1][0] = copy.deepcopy(NN2[seleccion[1][0]])
    seleccion[1][1] = copy.deepcopy(NN2[seleccion[1][1]])

    factor = 0

    NN1[0] = copy.deepcopy(seleccion[0][0])
    NN1[1] = copy.deepcopy(seleccion[0][1])
    NN2[0] = copy.deepcopy(seleccion[1][0])
    NN2[1] = copy.deepcopy(seleccion[1][1])

    for individuo in range(2, len(NN1)):
        if individuo % 2 == 0:
            NN1[individuo] = copy.deepcopy(seleccion[0][0])
            NN2[individuo] = copy.deepcopy(seleccion[1][0])
        else:
            NN1[individuo] = copy.deepcopy(seleccion[0][1])
            NN2[individuo] = copy.deepcopy(seleccion[1][1])

        NN1[individuo].mutarCapas(coeficienteMutacion)
        NN2[individuo].mutarCapas(coeficienteMutacion)

    Ut.pNoEs("Produccion: ")
    Ut.pNoEs(resultados[-1][0].produccion[0])
    Ut.pNoEs(" : ")
    Ut.pNoEs(resultados[-1][0].produccion[1])

NN1[0].guardarModelo('02_01_01_prueba')
NN2[0].guardarModelo('02_01_02_prueba')
