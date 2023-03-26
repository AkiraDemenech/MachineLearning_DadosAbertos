first_number = lambda s, end=1: ((first_number(s, end + 1) if end < len(s) and s[end].isdigit() else int(s[:end])) if s[
	0].isdigit() else first_number(s[1:])) if len(s) else None
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

crime_convert = lambda cr, crime_list: crime_list[cr] if type(cr) == int else crime_list.index(cr)

import pandas
import time
import os

timestamp = lambda lt=None: timestamp(time.localtime()) if lt == None else (lt[2::-1] + lt[3:6])
s_timestamp = lambda t=None: s_timestamp(timestamp()) if t == None else '%02d/%02d/%d %02d:%02d:%02d' % t

folder = './dados/'


def ibge(caminho=folder):
	ibge = {}
	raw_ibge = {}

	for arq in os.listdir(caminho):
		if arq.strip().lower().endswith('.xls'):

			ano = first_number(arq)
			print('\n' + s_timestamp() + '\t', ano, '\t', arq)

			if ano == None or ano < 1000:
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
				if pop_col[i] == None or type(pop_col[i]) == float or type(uf_col[i]) == float:
					continue

				ibge[ano][uf_col[i].strip()] = pop_col[i]

	return ibge, raw_ibge


'''
a = ibge()[0]
for k in a:
	print('\n', k)
	for uf in a[k]:
		print(uf,'\t', a[k][uf])
# '''


def seg_pub(arq=folder + 'indicadoressegurancapublicauf (1).xls', ibge_pop=None, full_pop = False, test_time = {(2021, 10), (2021, 11), (2021, 12)}):
	if ibge_pop == None:
		ibge_pop = ibge()[0]

	testes = {}
	seg_pub = {}  # dados do treinamento
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

		if not ano in ibge_pop:
			continue

		if full_pop:
			ln.update(ibge_pop[ano])
		else:
			ln['Pop'] = ibge_pop[ano][uf]

		dados = testes if (ano, mes) in test_time else seg_pub
		if not uf in dados:
			dados[uf] = []
		dados[uf].append(ln)

		#	ln['UF'] = uf
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

		if not uf in dados:
			dados[uf] = []
		dados[uf].append(ln)

		ln['Crime'] = crime_convert(crime, crimes)
		ln['Sexo'] = sex[sexo]
		ln['Ano'] = ano
		ln['Mês'] = mes
		ln['Ocorrências'] = vitim['Vítimas'][i]

	return seg_pub, testes, crimes


from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LinearRegression

dados, testes, tipos = seg_pub()


def treinar_testar(model, data, test, types, y_cols=['Ocorrências']):
	correct = []
	predicted = []

	for uf in data:
		print('\n', uf)
		x = []
		y = []

		x_cols = [c for c in data[uf][0] if not c in y_cols]

		print(x_cols, '\t', y_cols)
		for ln in data[uf]:
			x.append([ln[c] for c in x_cols])
			y.append([ln[c] for c in y_cols])

		model.fit(x, y)

		# Crime,Sexo,Pop,Ano,Mês -> Ocorrências
		for ln in test[uf]:
			x = [ln[c] for c in x_cols]
			y = model.predict([x])
			t = [ln[c] for c in y_cols]

			crime = crime_convert(x[x_cols.index('Crime')], types)
			sexo = sex[x[x_cols.index('Sexo')]]

			# [contexto], [entrada], [saída]
			correct.append(([uf, crime, sexo], x, t))
			predicted.append(([uf, crime, sexo], x, y))

		#	print(repr(crime), repr(sexo), x, '\t', y, t)
		#input()

	return correct, predicted


from sklearn.metrics import r2_score, mean_squared_error, accuracy_score, recall_score, f1_score, confusion_matrix

corretos, preditos = treinar_testar(LinearRegression(), dados, testes, tipos)

num_corretos = [o[0] for c, i, o in corretos]
num_preditos = [o[0][0] for c, i, o in preditos]

r2_score(num_corretos, num_preditos)
mean_squared_error(num_corretos, num_preditos)


corretos, preditos = treinar_testar(KNeighborsClassifier(n_neighbors=3), dados, testes, tipos)

num_corretos = [o[0] for c, i, o in corretos]
num_preditos = [o[0] for c, i, o in preditos]

confusion_matrix(num_corretos, num_preditos)
r2_score(num_corretos, num_preditos)
f1_score(num_corretos, num_preditos)
accuracy_score(num_corretos, num_preditos)
recall_score(num_corretos, num_preditos)

