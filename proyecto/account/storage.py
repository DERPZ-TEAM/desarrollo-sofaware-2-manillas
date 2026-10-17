"""
Almacenamiento de imágenes en Supabase Storage.

¿Por qué? Render borra su disco cada vez que se despliega una nueva versión,
así que las fotos subidas por el administrador se perderían. Supabase Storage
es un "bucket" (carpeta en la nube) que guarda los archivos para siempre y
entrega una URL pública para mostrarlos en la tienda.

Django usa esta clase automáticamente cuando existen las variables
SUPABASE_URL y SUPABASE_SERVICE_KEY (ver settings.py, sección STORAGES).

API REST de Supabase Storage usada:
    POST   {SUPABASE_URL}/storage/v1/object/{bucket}/{archivo}   -> subir
    DELETE {SUPABASE_URL}/storage/v1/object/{bucket}/{archivo}   -> borrar
    URL pública: {SUPABASE_URL}/storage/v1/object/public/{bucket}/{archivo}
"""
import logging
import mimetypes
import posixpath
import urllib.error
import urllib.request

from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

logger = logging.getLogger(__name__)


@deconstructible
class SupabaseStorage(Storage):

    def __init__(self):
        self.base_url = settings.SUPABASE_URL
        self.bucket = settings.SUPABASE_BUCKET
        self.key = settings.SUPABASE_SERVICE_KEY

    # El nombre guardado en la BD es 'productos/abc.jpg'. En el bucket los
    # archivos viven en la raíz ('abc.jpg'), igual que las imágenes que ya
    # se habían subido antes, así no se rompe ninguna URL existente.
    @staticmethod
    def _clave_en_bucket(name):
        return posixpath.basename(name)

    def _endpoint(self, name):
        return f'{self.base_url}/storage/v1/object/{self.bucket}/{self._clave_en_bucket(name)}'

    def _peticion(self, metodo, url, datos=None, tipo=None):
        cabeceras = {'Authorization': f'Bearer {self.key}', 'apikey': self.key}
        if tipo:
            cabeceras['Content-Type'] = tipo
            cabeceras['x-upsert'] = 'true'
        req = urllib.request.Request(url, data=datos, method=metodo, headers=cabeceras)
        return urllib.request.urlopen(req, timeout=30)

    def _save(self, name, content):
        content.seek(0)
        datos = content.read()
        tipo = getattr(content, 'content_type', None) or mimetypes.guess_type(name)[0] or 'image/jpeg'
        try:
            self._peticion('POST', self._endpoint(name), datos, tipo)
        except urllib.error.HTTPError as exc:
            detalle = exc.read().decode('utf-8', 'ignore')
            logger.error('Supabase rechazó la imagen %s: %s %s', name, exc.code, detalle)
            raise OSError('No se pudo guardar la imagen en Supabase Storage.') from exc
        except urllib.error.URLError as exc:
            logger.error('Sin conexión con Supabase Storage: %s', exc)
            raise OSError('No hay conexión con el servidor de imágenes.') from exc
        return name

    def delete(self, name):
        if not name:
            return
        try:
            self._peticion('DELETE', self._endpoint(name))
        except urllib.error.URLError as exc:
            # No detenemos la operación si la imagen vieja no se pudo borrar
            logger.warning('No se pudo borrar %s de Supabase: %s', name, exc)

    def exists(self, name):
        # Los nombres llevan un UUID aleatorio, así que nunca se repiten.
        return False

    def url(self, name):
        return (
            f'{self.base_url}/storage/v1/object/public/'
            f'{self.bucket}/{self._clave_en_bucket(name)}'
        )

    def size(self, name):
        return 0
