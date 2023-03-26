first_number = lambda s, end=1: ((first_number(s, end + 1) if end < len(s) and s[end].isdigit() else int(s[:end])) if s[0].isdigit() else first_number(s[1:])) if len(s) else None 

#import xlrd
import pandas 
import time
import os 

timestamp = lambda lt = None: timestamp(time.localtime()) if lt == None else (lt[2::-1] + lt[3:6])
s_timestamp = lambda t = None: s_timestamp(timestamp()) if t == None else '%02d/%02d/%d %02d:%02d:%02d' %t

caminho = './dados/'

ibge = {}

for arq in os.listdir(caminho):
	if arq.strip().lower().endswith('.xls'):	
		
		ano = first_number(arq)
		print('\n' + s_timestamp() + '\t', ano, '\t', arq)

		if ano == None or ano < 1000:
			continue

		print(s_timestamp(), '\tReading file....')	

		i = time.time_ns()
		ibge[ano] = pandas.read_excel(caminho + arq) 		
		f = time.time_ns()

		print(s_timestamp(), '\t',len(ibge[ano]), 'raw rows in',(f-i)/1000000,'ms')

#exit()
pop2020 = pandas.read_excel('IA/aprendizado de máquina/estimativa_dou_2020.xls')
pop2021 = pandas.read_excel('IA/aprendizado de máquina/estimativa_dou_2021 (1).xls')
print(pop2020)

seg_pub = pandas.read_excel('IA/aprendizado de máquina/indicadoressegurancapublicauf (1).xls')

meses = {}
for i in range(len(seg_pub)):
	if not seg_pub['Ano'][i] in meses:
		meses[seg_pub['Ano'][i]] = {}
	if not seg_pub['Mês'][i] in meses[seg_pub['Ano'][i]]: 	
		meses[seg_pub['Ano'][i]][seg_pub['Mês'][i]] = []
		

print(set(seg_pub['UF']))
print(meses[2022])