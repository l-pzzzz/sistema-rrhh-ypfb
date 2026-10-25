"""Archivos de prueba con la firma real de cada formato (RF-04)."""

from django.core.files.uploadedfile import SimpleUploadedFile

MB = 1024 * 1024


def pdf(nombre="documento.pdf", tamanio=1024):
    contenido = b"%PDF-1.4\n"
    return SimpleUploadedFile(nombre, contenido + b"0" * (tamanio - len(contenido)), content_type="application/pdf")


def png(nombre="foto.png"):
    return SimpleUploadedFile(nombre, b"\x89PNG\r\n\x1a\n" + b"0" * 100, content_type="image/png")


def jpg(nombre="foto.jpg"):
    return SimpleUploadedFile(nombre, b"\xff\xd8\xff\xe0" + b"0" * 100, content_type="image/jpeg")
