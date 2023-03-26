

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
sex.update({sex[s]:s for s in sex})

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


def seg_pub(arq=folder + 'indicadoressegurancapublicauf (1).xls', ibge_pop=None, full_pop = False, test_years = {2021}):
	if ibge_pop == None:
		ibge_pop = ibge()[0]

	testes = {}
	seg_pub = {} # dados do treinamento
	seg_pub_xls = pandas.ExcelFile(arq)
	ocorr = pandas.read_excel(seg_pub_xls, 'Ocorrências')
	vitim = pandas.read_excel(seg_pub_xls, 'Vítimas')
	
	crimes = list(set(vitim['Tipo Crime']).union(set(ocorr['Tipo Crime'])))
	crimes.sort()

	for i in range(len(ocorr)):

		crime = ocorr['Tipo Crime'][i]
		ano = ocorr['Ano'][i]
		uf = ocorr['UF'][i]
		ln = {}

		if not ano in ibge_pop:
			continue

		if full_pop:
			ln.update(ibge_pop[ano])
		else:	
			ln['Pop'] = ibge_pop[ano][uf]							

		dados = testes if ano in test_years else seg_pub
		if not uf in dados:
			dados[uf] = []
		dados[uf].append(ln)

		#	ln['UF'] = uf
		ln['Crime'] = crime_convert(crime, crimes)
		ln['Sexo'] = sex['Total']

		ln['Ano'] = ano
		ln['Mês'] = months[ocorr['Mês'][i].strip().lower()]
		ln['Ocorrências'] = ocorr['Ocorrências'][i]

	for i in range(len(vitim)):
		crime = vitim['Tipo Crime'][i]
		sexo = vitim['Sexo da Vítima'][i]
		ano = vitim['Ano'][i]
		uf = vitim['UF'][i]

		ln = {}

		if not ano in ibge_pop:
			continue 
		if full_pop:
			ln.update(ibge_pop[ano])
		else:	
			ln['Pop'] = ibge_pop[ano][uf]

		dados = testes if ano in test_years else seg_pub

		if not uf in dados:
			dados[uf] = []
		dados[uf].append(ln)

		ln['Crime'] = crime_convert(crime, crimes)
		ln['Sexo'] = sex[sexo]
		ln['Ano'] = ano
		ln['Mês'] = months[vitim['Mês'][i].strip().lower()]
		ln['Ocorrências'] = vitim['Vítimas'][i]

	return seg_pub, testes, crimes


from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier

data, test, types = seg_pub()
#print(data)
# UF
for uf in data:
	print('\n', uf)
	x = []
	y = []

	y_cols = ['Ocorrências']
	x_cols = [c for c in data[uf][0] if not c in y_cols]

	print(x_cols, '\t', y_cols)
	for ln in data[uf]:
		x.append([ln[c] for c in x_cols])
		y.append([ln[c] for c in y_cols])

	knn_model = KNeighborsClassifier(n_neighbors=3)
	knn_model.fit(x, y)
			
	# Crime,Sexo,Pop,Ano,Mês -> Ocorrências 
	for ln in test[uf]:
		x = [ln[c] for c in x_cols]
		y = knn_model.predict([x])
		t = [ln[c] for c in y_cols]		
		
		print(repr(crime_convert(x[x_cols.index('Crime')], types)),repr(sex[x[x_cols.index('Sexo')]]), x, '\t', y, t)
		input()
