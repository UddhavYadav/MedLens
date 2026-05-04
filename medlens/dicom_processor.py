import pydicom
import numpy as np
import io
from PIL import Image

def load_dicom(path):
    ds = pydicom.dcmread(path)
    img = ds.pixel_array.astype(np.float32)

    # Apply rescale slope/intercept
    slope = float(getattr(ds, "RescaleSlope", 1.0))
    intercept = float(getattr(ds, "RescaleIntercept", 0.0))
    img = img * slope + intercept

    return img, ds


def window_cxr(img):
    lo, hi = np.percentile(img, (1, 99))
    return np.clip(img, lo, hi)


def window_ct(img, center=40, width=400):
    lo = center - width / 2
    hi = center + width / 2
    return np.clip(img, lo, hi)


def normalize_to_uint8(img):
    img = img - img.min()
    img = img / (img.max() + 1e-6)
    img = (img * 255).astype(np.uint8)
    return img



def to_pil(img_uint8):
    pil = Image.fromarray(img_uint8, mode="L")
    return pil.convert("RGB")

def dicom_to_pil(path, modality="CXR"):
    img, ds = load_dicom(path)

    if modality == "CXR":
        img = window_cxr(img)
    elif modality == "CT":
        img = window_ct(img)

    img = normalize_to_uint8(img)
    return to_pil(img)




def to_bytes(img_uint8, format='PNG'):
    """
    Converts a uint8 numpy array to a byte stream of an image.

    Args:
        img_uint8 (np.ndarray): The image as a uint8 numpy array.
        format (str): The image format for the byte stream (e.g., 'PNG', 'JPEG').

    Returns:
        bytes: The image as a byte stream.
    """
    pil_image = Image.fromarray(img_uint8, mode="L")
    pil_image = pil_image.convert("RGB") # Maintain consistency with to_pil converting to RGB
    byte_arr = io.BytesIO()
    pil_image.save(byte_arr, format=format)
    return byte_arr.getvalue()


def dicom_to_bytes(path, modality="CXR", format='PNG'):
    """
    Loads a DICOM image, applies windowing and normalization, and returns it as a byte stream.

    Args:
        path (str): Path to the DICOM file.
        modality (str): Modality of the image ('CXR' or 'CT').
        format (str): The image format for the byte stream (e.g., 'PNG', 'JPEG').

    Returns:
        bytes: The processed image as a byte stream.
    """
    img, ds = load_dicom(path)

    if modality == "CXR":
        img = window_cxr(img)
    elif modality == "CT":
        img = window_ct(img)

    img = normalize_to_uint8(img)
    return to_bytes(img, format=format)