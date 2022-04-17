from legacy import Sim, Utilities as Ut
import copy
import RedNeuronal

# Modelo01_02 control de producto a fabricar - Genetico Colas
individuosPorEpoca = 10
generaciones = 40
tiempoSimulacion = 2000
individuosSeleccion = 2
coeficienteProduccion = 0.6
coeficienteColas = 10
coeficienteMutacionOriginal = -1
seleccion = [0, 0]

NN = []
resultados = []
fitness = []

simulador = Sim.Simulador01(logs=True)

colas = [[11, 12], [6, 7, 19, 20, 21, 22, 23, 32, 33], [8, 13, 14], [15, 25, 26, 27], [16, 17, 18], [29, 30]]

for i in range(0, individuosPorEpoca):
    NN.append(RedNeuronal.NN01_02(colas))

# for individuo in range(0, len(NN)):
#     NN[individuo].cargarModelo('01_02_g')

datafile = open('dataTrainingModelo01_02_g1.txt', 'a')

for generacion in range(0, 40):
    coeficienteMutacion = coeficienteMutacionOriginal  # + generacion / 200
    seleccion = [0, 0]
    print()
    Ut.pNoEs('Generacion ')
    print(generacion)
    resultados.append([])
    fitness.append([])
    for individuo in NN:
        simulador = Sim.Simulador01(logs=True)
        resultados[generacion].append(simulador.simular(individuo, tiempoSimulacion))

        fitness[generacion].append(individuo.fitness(resultados[generacion][-1], coeficienteProduccion, coeficienteColas))
        print(resultados[-1][-1].produccion)
        print(fitness[-1][-1])
    indice = 0

    for fitnessIndividuo in fitness[generacion]:
        if fitnessIndividuo > fitness[generacion][seleccion[0]]:
            seleccion[1] = copy.deepcopy(seleccion[0])
            seleccion[0] = copy.copy(indice)
        elif fitnessIndividuo > fitness[generacion][seleccion[1]]:
            seleccion[1] = copy.copy(indice)
        indice += 1
    datafile.writelines(str(fitness[generacion][seleccion[0]]) + '\n')

    seleccion[0] = copy.deepcopy(NN[seleccion[0]])
    seleccion[1] = copy.deepcopy(NN[seleccion[1]])

    factor = 0

    NN[0] = copy.deepcopy(seleccion[0])
    NN[1] = copy.deepcopy(seleccion[1])

    for individuo in range(2, len(NN)):
        if individuo % 2 == 0:
            NN[individuo] = copy.deepcopy(seleccion[0])
        else:
            NN[individuo] = copy.deepcopy(seleccion[1])
        NN[individuo].mutarCapas(coeficienteMutacion)

datafile.close()
# NN[0].guardarModelo('01_02_g')
