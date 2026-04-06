
from matplotlib import pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

import xarray as xr

ds = xr.open_dataset("hycom_out.nc")

u = ds['u-vel.']
v = ds['v-vel.']

mag = np.sqrt(u**2 + v**2)

var = mag

for i in range(len(var)):
    data = var[i][0]

    #
    #  Configura a projeção do mapa (PlateCarree é uma boa escolha para dados regulares)
    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Cria o plot de contorno preenchido


    lats = ds['lat']
    lons = ds['lon']
    ny, nx = ds.lat.shape

    X, Y = np.meshgrid(lons, lats)   # X.shape = (39,46), Y.shape = (39,46)

    # Agora plote com C = data_2d (shape 39,46)
    plot = ax.pcolormesh(lons, lats, data, shading='auto', cmap='viridis', transform=ccrs.PlateCarree())

    # Adiciona elementos do mapa
    ax.add_feature(cfeature.LAND, facecolor='lightgray')  # Adiciona continentes
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)     # Adiciona linhas de costa
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5) # Adiciona fronteiras (opcional)

    # Adiciona uma barra de cores
    cbar = plt.colorbar(plot, ax=ax, orientation='vertical', pad=0.05, shrink=0.7)
    cbar.set_label(f'Temperatura (°C)')

    # Adiciona título e grade
    plt.title(f'Campo de Temperatura - Camada {0}')
    ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)

    # Salva a figura (opcional)
    # plt.savefig('mapa_temperatura_hycom.png', dpi=300, bbox_inches='tight')

    # Exibe o mapa
    plt.savefig(f'fig/mag_{i}.png')
    plt.close('all')
    # plt.show()


# Plot de corrente

camada = 0
step = 5

for i in range(len(ds.time)):
    mag_i = mag[i, camada].values
    u_i = u[i, camada].values
    v_i = v[i, camada].values
    
    lons = ds['lon'].values
    lats = ds['lat'].values

    # Estatísticas para debug (imprimir uma vez)
    if i == 0:
        print(f"u range: {u_i.min():.3e} ~ {u_i.max():.3e}")
        print(f"v range: {v_i.min():.3e} ~ {v_i.max():.3e}")
        print(f"magnitude range: {mag_i.min():.3e} ~ {mag_i.max():.3e}")

    # Amostragem
    y_slice = slice(0, mag_i.shape[0], step)
    x_slice = slice(0, mag_i.shape[1], step)
    lons_sub = lons[y_slice, x_slice]
    lats_sub = lats[y_slice, x_slice]
    u_sub = u_i[y_slice, x_slice]
    v_sub = v_i[y_slice, x_slice]
    
    # Para evitar setas onde a corrente é muito fraca, defina um limiar
    mag_sub = np.sqrt(u_sub**2 + v_sub**2)
    mask = mag_sub > 0.01  # só plota setas com magnitude > 1 cm/s (ajuste)
    u_sub_masked = np.where(mask, u_sub, np.nan)
    v_sub_masked = np.where(mask, v_sub, np.nan)

    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Plot da magnitude
    plot = ax.pcolormesh(lons, lats, mag_i, shading='auto', 
                         cmap='viridis', transform=ccrs.PlateCarree())
    
    # ... dentro do loop, após definir u_sub, v_sub, lons_sub, lats_sub ...

    # Forçar que as setas sejam desenhadas com comprimento mínimo
    # Se os vetores são muito pequenos, multiplique por um fator de escala
    fator_escala = 50
    u_sub_vis = u_sub * fator_escala
    v_sub_vis = v_sub * fator_escala

    # Plotar setas com escala manual, sem auto-escala
    q = ax.quiver(lons_sub, lats_sub, u_sub_vis, v_sub_vis,
                angles='xy', scale_units='xy', scale=1,
                color='black', width=0.005, 
                headwidth=3, headlength=4, headaxislength=4,
                transform=ccrs.PlateCarree())

    # Adicionar uma seta de referência explicando o fator
    ax.quiverkey(q, 0.85, 0.1, 0.1, 
                f'{0.1/fator_escala:.2f} m/s', 
                labelpos='E', coordinates='figure', color='black')
    
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    
    cbar = plt.colorbar(plot, ax=ax, orientation='vertical', pad=0.05, shrink=0.7)
    cbar.set_label('Magnitude da velocidade (m/s)')
    
    # tempo_str = np.datetime_as_string(ds.time[i].values, unit='h')
    plt.title(f'Correntes - Camada {camada} - {int(ds.time[i])}')
    ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)

    plt.savefig(f'fig/corrente_{i}.png', dpi=300, bbox_inches='tight')
    plt.close()