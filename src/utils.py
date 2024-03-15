from pydantic import BaseModel
from google.cloud import storage
from google.cloud import datastore

class FormData(BaseModel):
  timestamp: int
  string_qr: str


database_name = 'registro'
datastore_client = datastore.Client(database = database_name)

def create_and_store_entity(form_data: FormData):
  kind = FormData.__name__
  form_key = datastore_client.key(kind)

  form_entity = datastore.Entity(key = form_key)
  form_entity.update({
    'timestamp': form_data.timestamp,
    'string_qr': form_data.string_qr,
  })

  datastore_client.put(form_entity)

  return form_data


def cors_configuration(bucket_name: str):
  """Set a bucket's CORS policies configuration."""

  storage_client = storage.Client()

  bucket = storage_client.get_bucket(bucket_name)
  bucket.cors = [
    {
      'origin': ['*'],
      'responseHeader': [
        'Content-Type',
        'x-goog-resumable',
      ],
      'method': ['PUT', 'POST'],
      'maxAgeSeconds': 3600,
    },
  ]

  bucket.patch()
