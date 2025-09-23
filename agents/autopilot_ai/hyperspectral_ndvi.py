# NDVI из ENVI (гиперспектр) через spectral
# pip install spectral numpy pillow
import numpy as np
import spectral as sp
from PIL import Image

def compute_ndvi(envi_hdr_path: str, red_nm: int = 650, nir_nm: int = 800, save_png: str = "ndvi.png"):
    img = sp.open_image(envi_hdr_path)   # .hdr (ENVI) -> lazy loader
    # Поиск ближайших индексов к заданным длинам волн
    wl = np.array(img.bands.centers)  # список длин волн
    red_idx = (np.abs(wl - red_nm)).argmin()
    nir_idx = (np.abs(wl - nir_nm)).argmin()

    red = img[:, :, red_idx].astype(np.float32)
    nir = img[:, :, nir_idx].astype(np.float32)
    ndvi = (nir - red) / (nir + red + 1e-6)
    # нормируем 0..255 для предпросмотра
    ndvi_img = ((ndvi + 1.0) * 127.5).clip(0, 255).astype(np.uint8)
    Image.fromarray(ndvi_img).save(save_png)
    return save_png

if __name__ == "__main__":
    # пример: compute_ndvi("data/hyperspec_scene.hdr")
    pass