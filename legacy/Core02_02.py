from legacy import Sim, Utilities as Ut
import copy
import RedNeuronal

# Modelo02_02 control de bifurcaciones - Genetico Colas
individuosPorGeneracion = 6
generaciones = 10
tiempoSimulacion = 2000
coeficienteProduccion = 0.8
coeficienteColas = 0.2
coeficienteMutacion = 0.15
seleccion = [[0, 0], [0, 0]]

NN1 = []
NN2 = []
resultados = []
fitness = []

simulador = Sim.Simulador02(logs=True)

colas1 = [[11, 12], [6, 7, 19, 20, 21, 22, 23, 32, 33], [8, 13, 14], [15, 25, 26, 27], [16, 17, 18], [29, 30]]
colas2 = [[11, 12], [6, 7, 19, 20, 21, 22, 23, 32, 33], [8, 13, 14], [15, 25, 26, 27], [16, 17, 18], [29, 30]]

for i in range(0, individuosPorGeneracion):
    NN1.append(RedNeuronal.NN02_02_01(colas1))
for i in range(0, individuosPorGeneracion):
    NN2.append(RedNeuronal.NN02_02_02(colas2))

for individuo in range(0, len(NN1)):
    NN1[individuo].cargarModelo('02_03_01_v2')

for individuo in range(0, len(NN2)):
    NN2[individuo].cargarModelo('02_03_02_v2')

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
        Ut.pNoEs(resultados[-1][-1].produccion[0])
        Ut.pNoEs(" : ")
        print(resultados[-1][-1].produccion[1])
    indice = 0
    for fitnessIndividuo in fitness[generacion]:
        if fitnessIndividuo[0] > fitness[generacion][seleccion[0][0]][0]:
            seleccion[0][1] = copy.copy(seleccion[0][0])
            seleccion[0][0] = copy.copy(indice)
        elif fitnessIndividuo[0] > fitness[generacion][seleccion[0][1]][0]:
            seleccion[0][1] = copy.copy(indice)
        if fitnessIndividuo[1] > fitness[generacion][seleccion[1][0]][1]:
            seleccion[1][1] = copy.copy(seleccion[0][0])
            seleccion[1][0] = copy.copy(indice)
        elif fitnessIndividuo[1] > fitness[generacion][seleccion[1][1]][1]:
            seleccion[1][1] = copy.copy(indice)
        indice += 1

    seleccion[0][0] = copy.copy(NN1[seleccion[0][0]])
    seleccion[0][1] = copy.copy(NN1[seleccion[0][1]])
    seleccion[1][0] = copy.copy(NN2[seleccion[1][0]])
    seleccion[1][1] = copy.copy(NN2[seleccion[1][1]])

    NN1[0] = copy.copy(seleccion[0][0])
    NN1[1] = copy.copy(seleccion[0][1])
    NN2[0] = copy.copy(seleccion[1][0])
    NN2[1] = copy.copy(seleccion[1][1])

    for individuo in range(2, len(NN1)):
        if individuo % 2 == 0:
            NN1[individuo] = copy.copy(seleccion[0][0])
            NN2[individuo] = copy.copy(seleccion[1][0])
        else:
            NN1[individuo] = copy.copy(seleccion[0][1])
            NN2[individuo] = copy.copy(seleccion[1][1])

        NN1[individuo].mutarCapas(coeficienteMutacion)
        NN2[individuo].mutarCapas(coeficienteMutacion)

NN1[0].guardarModelo('02_04_01')
NN2[0].guardarModelo('02_04_02')
