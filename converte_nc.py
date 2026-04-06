import glob
import re
import os
import numpy as np
import xarray as xr
import pandas as pd

import sys
sys.path.append('HYCOM-utilities/python')
from hycom.io import read_hycom_fields, read_hycom_coords

# ------------------------------------------------------------
# 1. Funções auxiliares
# ------------------------------------------------------------

def extrair_tempo_do_nome(arquivo):
    """
    Extrai o timestamp do nome do arquivo HYCOM.
    Exemplo esperado: 'archv.2020_123_12.a' -> 2020-05-02 12:00:00
    """
    nome = os.path.basename(arquivo)
    # Padrão: archv.AAAA_DDD_HH.a
    match = re.search(r'archv\.(\d{4})_(\d{3})_(\d{2})', nome)
    if match:
        ano, doy, hora = match.groups()
        data = pd.to_datetime(f"{ano}-{doy}", format="%Y-%j")
        data = data + pd.Timedelta(hours=int(hora))
        return data
    else:
        # Se não encontrar, retorna None (você pode tentar ler do arquivo .b)
        return None

def extrair_tempo_do_b(arquivo_b):
    """
    Lê o model day do arquivo .b (fallback caso o nome não tenha data).
    """
    with open(arquivo_b, 'r') as f:
        linhas = f.readlines()
    # A primeira linha de campo (após o cabeçalho) contém o model day
    for linha in linhas[9:]:
        partes = linha.split()
        if len(partes) >= 4:
            # Formato: campo '=' time_step model_day ...
            try:
                tempo_modelo = float(partes[3])
                return tempo_modelo
            except:
                continue
    return None

# ------------------------------------------------------------
# 2. Função principal
# ------------------------------------------------------------

def converter_hycom_para_netcdf(pasta_entrada, arquivo_saida, arquivo_coord, campos=None, camadas=None):
    """
    Converte todos os arquivos .a de uma pasta em um único NetCDF.

    Parâmetros
    ----------
    pasta_entrada : str
        Caminho para a pasta com os arquivos .a e .b.
    arquivo_saida : str
        Nome do arquivo NetCDF de saída (ex.: 'dados_completos.nc').
    arquivo_coord : str
        Caminho para o arquivo 'regional.grid' (sem extensão).
    campos : list, opcional
        Lista de campos a serem extraídos (ex.: ['temp', 'salin']).
        Se None, lê todos os campos disponíveis.
    camadas : list, opcional
        Lista de índices das camadas verticais a serem lidas (ex.: [0,1,2]).
        Se None, lê todas as camadas.
    """

    # --- Leitura das coordenadas (uma única vez) ---
    print("Lendo coordenadas do grid...")
    coords = read_hycom_coords(arquivo_coord, fields=['plat', 'plon'])
    lats = coords['plat']   # shape (jdm, idm)
    lons = coords['plon']   # shape (jdm, idm)

    # --- Listagem e ordenação dos arquivos ---
    arquivos_a = sorted(glob.glob(os.path.join(pasta_entrada, '*.a')))
    if not arquivos_a:
        raise FileNotFoundError(f"Nenhum arquivo .a encontrado em {pasta_entrada}")

    print(f"Encontrados {len(arquivos_a)} arquivos.")

    datasets = []
    tempos = []

    # --- Loop sobre cada arquivo ---
    for arq_a in arquivos_a:
        if 'dummy' in arq_a:
            continue
        base = arq_a[:-2]            # remove extensão .a
        arq_b = base + '.b'

        # 2.1. Determinar o tempo
        # funcao ta esquisita -> USA A DO B
        # tempo = extrair_tempo_do_nome(arq_a)
        tempo = None
        if tempo is None:
            print(f"  Não foi possível extrair data do nome de {arq_a}, tentando .b...")
            model_day = extrair_tempo_do_b(arq_b)
            if model_day is not None:
                tempo = model_day   # aqui você pode converter model_day para datetime se tiver a referência
            else:
                print(f"  Pulando {arq_a} (não foi possível determinar o tempo).")
                continue

        print(f"  Processando {os.path.basename(arq_a)} (tempo = {tempo})...")

        # 2.2. Ler os campos desejados
        # camadas = [] pega todas EU ACHO
        dados = read_hycom_fields(arq_a, fields=campos if campos else [], layers=camadas, replace_to_nan=True)

        # 2.3. Montar um xarray.Dataset para este instante
        ds = xr.Dataset()
        for nome_campo, arr in dados.items():
            # arr.shape = (num_camadas, lat, lon)
            ds[nome_campo] = xr.DataArray(
                arr,
                dims=['layer', 'y', 'x'],
                coords={
                    'layer': np.arange(arr.shape[0]),
                    'y': np.arange(arr.shape[1]),
                    'x': np.arange(arr.shape[2])
                }
            )

        # 2.4. Incluir as coordenadas geográficas
        ds = ds.assign_coords({
            'lat': (('y', 'x'), lats),
            'lon': (('y', 'x'), lons)
        })

        # 2.5. Adicionar a dimensão tempo
        ds = ds.expand_dims(time=[tempo])
        datasets.append(ds)
        tempos.append(tempo)

    # --- 3. Concatenar tudo ao longo do tempo ---
    print("Concatenando os datasets...")
    combinado = xr.concat(datasets, dim='time')
    # Ordenar pelo tempo (garantia)
    combinado = combinado.sortby('time')

    # --- 4. Salvar em NetCDF ---
    print(f"Salvando em {arquivo_saida}...")
    combinado.to_netcdf(arquivo_saida)
    print("Concluído!")

# ------------------------------------------------------------
# 3. Exemplo de uso (ajuste os caminhos conforme sua máquina)
# ------------------------------------------------------------
if __name__ == "__main__":
    converter_hycom_para_netcdf(
        pasta_entrada="/Users/breno/Projetos/tutorial_hycom/tar_001/",
        arquivo_saida="hycom_out.nc",
        arquivo_coord="data/regional.grid",
        campos = [],
        # campos=[None], # SE DEIXAR SEM NADA ELE PEGA TUDO 
        camadas=[]
    )


# fazendo um plot bobo
''''
ds = xr.open_dataset("hycom_out.nc")

for i in ds.time:
    i = int(i)
    ds['u-vel.'][i].plot()
    plt.savefig(f'uvel_{i}')
    plt.close('all')
'''
