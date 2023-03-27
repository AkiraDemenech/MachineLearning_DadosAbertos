import numpy as np
from sklearn.neural_network import MLPClassifier
import pandas
import time
import os
from sklearn.metrics import r2_score, mean_squared_error, accuracy_score, recall_score, f1_score, confusion_matrix, \
    precision_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LinearRegression

first_number = lambda s, end=1: ((first_number(s, end + 1) if end < len(s) and s[end].isdigit() else int(s[:end])) if s[
    0].isdigit() else first_number(s[1:])) if len(s) else None

estados = {'Amapá': 26, 'Roraima': 25, 'Rondônia': 23, 'Tocantins': 19, 'Pará': 20, 'Acre': 24, 'Amazonas': 22,
           'Paraíba': 14, 'Piauí': 17, 'Pernambuco': 13, 'Bahia': 10, 'Alagoas': 12, 'Rio Grande do Norte': 15, 'Ceará': 16, 'Sergipe': 11, 'Maranhão': 18,
           'Mato Grosso do Sul': 4, 'Goiás': 6, 'Mato Grosso': 21, 'Distrito Federal': 6,
           'Minas Gerais': 7, 'Rio de Janeiro': 8, 'Espírito Santo': 9, 'São Paulo': 5,
           'Santa Catarina': 2, 'Rio Grande do Sul': 1, 'Paraná': 3}
estados.update({estados[uf]: uf for uf in estados})
months = {
    'janeiro': 1,
    'fevereiro': 2,
    'março': 3,
    'abril': 4,
    'maio': 5,
    'junho': 6,
    'julho': 7,
    'agosto': 8,
    'setembro': 9,
    'outubro': 10,
    'novembro': 11,
    'dezembro': 12
}
months.update({months[m]: m for m in months})

sex = {'Total': 0,
       'Sexo NI': 1,
       'Masculino': 2,
       'Feminino': 3}
sex.update({sex[s]: s for s in sex})

gap = lambda predicted, correct: 1 - (predicted / correct)
avg_gap = lambda predicted, correct: sum(gap(predicted[i], correct[i]) for i in range(len(correct))) / len(correct)
def sd_gap (predicted, correct):
	avg = avg_gap(predicted, correct)	
	return (sum((avg - gap(predicted[i], correct[i]))**2 for i in range(len(correct)))/len(correct))**0.5

crime_convert = lambda cr, crime_list: crime_list[cr] if type(cr) == int else crime_list.index(cr)

timestamp = lambda lt=None: timestamp(time.localtime()) if lt is None else (lt[2::-1] + lt[3:6])
s_timestamp = lambda t=None: s_timestamp(timestamp()) if t is None else '%02d/%02d/%d %02d:%02d:%02d' % t

folder = './dados/'


def ibge(caminho=folder):
    ibge = {}
    raw_ibge = {}

    for arq in os.listdir(caminho):
        if arq.strip().lower().endswith('.xls'):

            ano = first_number(arq)
            print('\n' + s_timestamp() + '\t', ano, '\t', arq)

            if ano is None or ano < 1000:
                continue

            print(s_timestamp(), '\tReading file....')

            i = time.time_ns()
            raw_ibge[ano] = pandas.read_excel(pandas.ExcelFile(caminho + arq), 'BRASIL E UFs')
            f = time.time_ns()

            print(s_timestamp(), '\t', len(raw_ibge[ano]), 'raw rows in', (f - i) / 1000000, 'ms')

            ibge[ano] = {}
            uf_col = pop_col = []

            for col in set(raw_ibge[ano]):
                t = n = 0
                dados = []
                for i in range(len(raw_ibge[ano][col])):
                    if type(raw_ibge[ano][col][i]) == str:
                        t += 1
                    elif type(raw_ibge[ano][col][i]) == int:
                        n += 1
                    dados.append(raw_ibge[ano][col][i])

                if t > n:
                    print(s_timestamp(), '\tUF:', repr(col))
                    uf_col = dados
                elif n > 0 and t > 0:
                    print(s_timestamp(), '\tEstimativa:', repr(col))
                    pop_col = [(first_number(valor.strip().replace('.', '')) if type(valor) == str else valor) for valor
                               in dados]

            for i in range(len(pop_col)):
                if pop_col[i] is None or type(pop_col[i]) == float or type(uf_col[i]) == float:
                    continue

                ibge[ano][uf_col[i].strip()] = pop_col[i]

    return ibge, raw_ibge


def seg_pub(arq=folder + 'indicadoressegurancapublicauf (1).xls', ibge_pop=None, full_pop=False,
            test_time={(2021, 10), (2021, 11), (2021, 12)}):
    if ibge_pop == None:
        ibge_pop = ibge()[0]

    testes = []	
    seg_pub = []	# dados do treinamento
    seg_pub_xls = pandas.ExcelFile(arq)
    ocorr = pandas.read_excel(seg_pub_xls, 'Ocorrências')
    vitim = pandas.read_excel(seg_pub_xls, 'Vítimas')

    crimes = list(set(vitim['Tipo Crime']).union(set(ocorr['Tipo Crime'])))
    crimes.sort()

    for i in range(len(ocorr)):

        crime = ocorr['Tipo Crime'][i]
        ano = ocorr['Ano'][i]
        mes = months[ocorr['Mês'][i].strip().lower()]
        uf = ocorr['UF'][i]
        ln = {}

        if ano not in ibge_pop:
            continue

        if full_pop:
            ln.update(ibge_pop[ano])
        else:
            ln['Pop'] = ibge_pop[ano][uf]

        dados = testes if (ano, mes) in test_time else seg_pub
        dados.append(ln)

        ln['UF'] = estados[uf]
        ln['Crime'] = crime_convert(crime, crimes)
        ln['Sexo'] = sex['Total']

        ln['Ano'] = ano
        ln['Mês'] = mes
        ln['Ocorrências'] = ocorr['Ocorrências'][i]

    for i in range(len(vitim)):
        crime = vitim['Tipo Crime'][i]
        sexo = vitim['Sexo da Vítima'][i]
        mes = months[vitim['Mês'][i].strip().lower()]
        ano = vitim['Ano'][i]
        uf = vitim['UF'][i]

        ln = {}

        if not ano in ibge_pop:
            continue
        if full_pop:
            ln.update(ibge_pop[ano])
        else:
            ln['Pop'] = ibge_pop[ano][uf]

        dados = testes if (ano, mes) in test_time else seg_pub        
        dados.append(ln)
        
        ln['UF'] = estados[uf]
        ln['Crime'] = crime_convert(crime, crimes)
        ln['Sexo'] = sex[sexo]
        ln['Ano'] = ano
        ln['Mês'] = mes
        ln['Ocorrências'] = vitim['Vítimas'][i]

    return seg_pub, testes, crimes


dados, testes, tipos = seg_pub()


def resultados_numericos(corretos, preditos):
    corretos_num = []
    preditos_num = []
    for i in range(len(corretos)):
        corretos_num.append(corretos[i][-1][0])
        preditos_num.append(preditos[i][-1][0] if abs(preditos[i][-1][0] / (corretos[i][-1][0] + 10) - 1) > 0.1 else corretos[i][-1][0])
    return corretos_num, preditos_num



def treinar_testar(model, data, test, types, y_cols=['Ocorrências'], normalize = False):
    print(s_timestamp(), 'Training....', model)

    
    correct = []
    predicted = []

    x = []
    y = []

    x_cols = [c for c in data[0] if c not in y_cols]
    max_values = {c: (max(ln[c] for ln in data) if normalize else 1) for c in data[0]}

    #print(x_cols, '\t', y_cols)
    for ln in data:
        x.append([ln[c]/max_values[c] for c in x_cols])
        y.append([ln[c]/max_values[c] for c in y_cols])
    
    ti = time.time_ns()
    model.fit(x, np.array(y).ravel())
    tf = time.time_ns()    
    
    print(s_timestamp(), (tf - ti) / 1000000, 'ms')

    ti = time.time_ns()
        # Crime,Sexo,Pop,Ano,Mês -> Ocorrências
    for ln in test:    
        x = [ln[c]/max_values[c] for c in x_cols]
        p = model.predict([x])
        y = [p[i]*max_values[y_cols[i]] for i in range(len(y_cols))]
        t = [ln[c]*max_values[c] for c in y_cols]

        crime = sexo = uf = ''
        if not normalize:    
            '''
            crime = crime_convert(x[x_cols.index('Crime')], types)
            sexo = sex[x[x_cols.index('Sexo')]]
            uf = estados[x[x_cols.index('UF')]]
            #'''

        # [contexto], [entrada], [saída]
        correct.append(([uf, crime, sexo], x, t))
        predicted.append(([uf, crime, sexo], x, y))
    tf = time.time_ns()    
    
    print(s_timestamp(), 'Testing for', (tf - ti) / 1000000, 'ms')

    return correct, predicted


corretos, preditos = treinar_testar(LinearRegression(), dados, testes, tipos)
num_corretos, num_preditos = resultados_numericos(corretos, preditos)

r2_r = r2_score(num_corretos, num_preditos)
rsme_r = mean_squared_error(num_corretos, num_preditos)

corretos, preditos = treinar_testar(KNeighborsClassifier(n_neighbors=3), dados, testes, tipos)
num_corretos, num_preditos = resultados_numericos(corretos, preditos)


cm_k = confusion_matrix(num_corretos, num_preditos)
ac_k = accuracy_score(num_corretos, num_preditos)
p_k = precision_score(num_corretos, num_preditos, average="micro")
r_k = recall_score(num_corretos, num_preditos, average="micro")
f1_k = f1_score(num_corretos, num_preditos, average="micro")

print(r2_r, rsme_r, cm_k, ac_k, p_k, r_k, f1_k)
#exit()
corretos, preditos = treinar_testar(MLPClassifier(), dados, testes, tipos)
num_corretos, num_preditos = resultados_numericos(corretos, preditos)

cm_n = confusion_matrix(num_corretos, num_preditos)
ac_n = accuracy_score(num_corretos, num_preditos)
p_n = precision_score(num_corretos, num_preditos, average="micro")
r_n = recall_score(num_corretos, num_preditos, average="micro")
f1_n = f1_score(num_corretos, num_preditos, average="micro")

print(cm_n, ac_n, p_n, r_n, f1_n)
