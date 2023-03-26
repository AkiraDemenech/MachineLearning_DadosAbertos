first_number = lambda s, end=1: ((first_number(s, end + 1) if end < len(s) and s[end].isdigit() else int(s[:end])) if s[0].isdigit() else first_number(s[1:])) if len(s) else None 
months = {
	'janeiro':	1,
	'fevereiro':	2,
	'março':	3,
	'abril':	4,
	'maio':	5,
	'junho':	6,
	'julho':	7,
	'agosto':	8,
	'setembro':	9,
	'outubro':	10,
	'novembro':	11,
	'dezembro':	12
	}

#import xlrd
import pandas 
import time
import os 

timestamp = lambda lt = None: timestamp(time.localtime()) if lt == None else (lt[2::-1] + lt[3:6])
s_timestamp = lambda t = None: s_timestamp(timestamp()) if t == None else '%02d/%02d/%d %02d:%02d:%02d' %t

def ibge (caminho = './dados/'):

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

			print(s_timestamp(), '\t',len(raw_ibge[ano]), 'raw rows in',(f-i)/1000000,'ms')

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
					pop_col = [(first_number(valor.strip().replace('.','')) if type(valor) == str else valor) for valor in dados]
				 									

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

def seg_pub (arq = './dados/indicadoressegurancapublicauf (1).xls', ibge_pop = None):

	if ibge_pop == None:
		ibge_pop = ibge()[0]

	seg_pub = {}
	seg_pub_xls = pandas.ExcelFile(arq)
	ocorr = pandas.read_excel(seg_pub_xls, 'Ocorrências')
	vitim = pandas.read_excel(seg_pub_xls, 'Vítimas')

	for i in range(len(ocorr)):
		crime = ocorr[i]['Tipo Crime']
		ano = ocorr[i]['Ano']
		uf = ocorr[i]['UF']
		ln = dict(ibge_pop[ano])
		
		if not uf in seg_pub:
			seg_pub[uf] = {}
		if not crime in seg_pub[uf]:
			seg_pub[uf][crime] = {}
		seg_pub[uf][crime]['Total'] = ln	

	#	ln['UF'] = ocorr[i]['UF']
	#	ln['Crime'] = ocorr[i]['Tipo Crime']
	#	ln['Sexo'] = 'Total'
		
		ln['Ano'] = ano
		ln['Mês'] = months(ocorr[i]['Mês'].strip().lower())
		ln['Ocorrências'] = ocorr[i]['Ocorrências']

	for i in range(len(vitim)):	
		crime = vitim[i]['Tipo Crime']
		ano = vitim[i]['Ano']
		uf = vitim[i]['UF']
		ln = dict(ibge_pop[ano])
		
		if not uf in seg_pub:
			seg_pub[uf] = {}
		if not crime in seg_pub[uf]:
			seg_pub[uf][crime] = {}
		seg_pub[uf][crime][vitim[i]['Sexo da Vítima']] = ln

		ln['Ano'] = ano
		ln['Mês'] = months(vitim[i]['Mês'].strip().lower())
		ln['Ocorrências'] = vitim[i]['Vítimas']
		
	return seg_pub
		

