import Sim
import copy
import RedNeuronal
import Utilities as Ut

# Modelo01_01 control de producto a fabricar - Genetico
individuosPorEpoca = 10
generaciones = 40
tiempoSimulacion = 2000
individuosSeleccion = 2
coeficienteProduccion = 0.6
coeficienteColas = 10
coeficienteMutacionOriginal = -2
seleccion = [0, 0]

NN = []
resultados = []
fitness = []

simulador = Sim.Simulador01(logs=True)

retenedoresEntrada01 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
                        20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33]

for i in range(0, individuosPorEpoca):
    NN.append(RedNeuronal.NN01_01(retenedoresEntrada01, simulador.modeloPlanta))

# for individuo in range(0, len(NN)):
# NN[individuo].cargarModelo('01_01_c')

datafile = open('dataTrainingModelo01_01_d.txt', 'a')

for generacion in range(0, 100):
    coeficienteMutacion = coeficienteMutacionOriginal + generacion / 200
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

NN[0].guardarModelo('01_01_d')
datafile.close()
