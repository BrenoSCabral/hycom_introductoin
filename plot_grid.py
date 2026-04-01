import numpy as np
import matplotlib.pyplot as plt

idm = 46
jdm = 39

# função para ler campo HYCOM
def read_hycom_field(filename, record, idm, jdm):
    data = np.fromfile(filename, dtype='>f4')
    n2drec = ((idm*jdm + 4095)//4096)*4096
    
    start = record * n2drec
    end   = start + idm*jdm
    
    field = data[start:start + n2drec][:idm*jdm]
    return field.reshape((jdm, idm))

plon = read_hycom_field('data/regional.grid.a', 0, idm, jdm)
plat = read_hycom_field('data/regional.grid.a', 1, idm, jdm)

plon = np.where(plon > 180, plon - 360, plon)


depth = np.fromfile('data/depth_XXXxr.rr_01.a', dtype='>f4')

depth = depth[:idm*jdm].reshape((jdm, idm))

# remover valores absurdos (HYCOM missing)
depth[depth > 1e20] = np.nan


plt.figure(figsize=(8,6))
plt.contourf(plon, plat, depth, levels=30) # -> Esse cara vai ter um "corretivo" pra ficar mais bonito de ver
# plt.pcolormesh(plon, plat, depth, shading='auto')


plt.scatter(plon, plat, s=1, color='k')

plt.colorbar(label='Depth (m)')

plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('HYCOM Bathymetry (Real Coordinates)')

plt.tight_layout()
plt.savefig('fig/grid.png')