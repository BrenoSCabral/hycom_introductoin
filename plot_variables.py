import numpy as np
import matplotlib.pyplot as plt

idm = 46
jdm = 39

def read_field(filename, record):
    data = np.fromfile(filename, dtype='>f4')
    n2drec = ((idm*jdm + 4095)//4096)*4096
    
    start = record * n2drec
    field = data[start:start+n2drec][:idm*jdm]
    
    return field.reshape((jdm, idm))

plon = read_field('data/regional.grid.a', 0)
plat = read_field('data/regional.grid.a', 1)

plon = np.where(plon > 180, plon - 360, plon)

# =========================
# BATHYMETRY
# =========================
depth = read_field('data/depth_XXXxr.rr_01.a', 0)
depth[depth > 1e20] = np.nan

# máscara derivada
mask = np.where(depth > 0, 1, 0)


# k varia entre 0 e 11
k = 0

# stress do vento

tau_x = read_field('data/tauewd.a', k)
tau_y = read_field('data/taunwd.a', k)

# limpar valores inválidos
tau_x[tau_x > 1e20] = np.nan
tau_y[tau_y > 1e20] = np.nan


mag = np.sqrt(tau_x**2 + tau_y**2)



plt.figure(figsize=(8,6))

plt.pcolormesh(plon, plat, mag, shading='auto')
plt.colorbar(label='Wind stress magnitude')

plt.quiver(plon, plat, tau_x, tau_y)
plt.contourf(plon, plat, mask,
             levels=[-0.1, 0.5],   # pega só terra (0)
             colors='black',
             alpha=0.6)
plt.title('Wind Stress Magnitude')

plt.savefig('fig/wind_stress.png')
plt.close('all')

# fluxo
for k in range(0,5):
    shflux = read_field('data/shwflx.a', k)
    shflux[shflux > 1e20] = np.nan

    plt.figure(figsize=(8,6))

    plt.pcolormesh(plon, plat, shflux, shading='auto')
    plt.colorbar(label='Heat flux')

    plt.contourf(plon, plat, mask,
                levels=[-0.1, 0.5],   # pega só terra (0)
                colors='black',
                alpha=0.6)
    plt.title('Surface Heat Flux')

    plt.savefig(f'fig/surface_heat_flux_{k}.png')
    plt.close('all')

# precip
prec = read_field('data/precip.a', 0)
prec[prec > 1e20] = np.nan

plt.figure(figsize=(8,6))
plt.pcolormesh(plon, plat, prec, shading='auto')
plt.colorbar(label='Precipitation')
plt.title('Precipitation')
plt.savefig('fig/prec.png')
plt.close('all')