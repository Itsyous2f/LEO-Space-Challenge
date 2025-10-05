import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

# Open the EMIT NetCDF dataset
ds = xr.open_dataset("emit_data/EMIT_L2B_MIN_001_20251002T064804_2527504_055.nc")

# Extract band depth and mineral ID arrays
bd1 = ds["group_1_band_depth"].values
bd2 = ds["group_2_band_depth"].values
gid1 = ds["group_1_mineral_id"].values
gid2 = ds["group_2_mineral_id"].values

# Mask out pixels with no mineral detected (ID = 0)
bd1_masked = np.where(gid1 != 0, bd1, np.nan)
bd2_masked = np.where(gid2 != 0, bd2, np.nan)

# Function to plot heatmap with scale
def plot_heatmap(data, title, ax):
    im = ax.imshow(data, cmap='coolwarm', vmin=0, vmax=1)  # set depth scale from 0 to 1
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Band Depth (0=none, 1=strongest)')
    ax.set_title(title)
    ax.set_xlabel('Crosstrack')
    ax.set_ylabel('Downtrack')

# Create figure
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Plot Group 1
plot_heatmap(bd1_masked, "Group 1 Band Depth Heatmap", axes[0])

# Plot Group 2
plot_heatmap(bd2_masked, "Group 2 Band Depth Heatmap", axes[1])

plt.tight_layout()
plt.show()
