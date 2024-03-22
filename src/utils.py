from pydantic import BaseModel
from google.cloud import storage
from google.cloud import datastore

class FormData(BaseModel):
  timestamp: int
  name: str
  dni: str
  birth_date: int


database_name = 'registro'
datastore_client = datastore.Client(database = database_name)

def create_and_store_entity(form_data: FormData):
  kind = FormData.__name__
  form_key = datastore_client.key(kind)

  form_entity = datastore.Entity(key = form_key)
  form_entity.update(form_data)

  datastore_client.put(form_entity)

  return form_data


def get_all_entities():
  query = datastore_client.query(kind = FormData.__name__)
  result: list[FormData] = list(query.fetch())

  return result


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
