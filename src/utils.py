from fastapi import UploadFile
from pydantic import BaseModel
from google.cloud import storage, datastore


class APIModel(BaseModel):
  creation_date: str
  name: str
  dni: str
  birth_date: str
  photo_url: str | None = None

database_name = 'registro'
datastore_client = datastore.Client(database = database_name)

def create_and_store_entity(form_data: APIModel):
  kind = APIModel.__name__
  form_key = datastore_client.key(kind)

  form_entity = datastore.Entity(key = form_key)
  form_entity.update(form_data)

  datastore_client.put(form_entity)

  return form_data


def get_all_entities(filterValue: str | None = None):
  query = datastore_client.query(kind = APIModel.__name__)

  entities: list[APIModel] = list(query.fetch())

  if filterValue != None:
    entities = list(filter(lambda object: is_value_in_object(filterValue, object), entities))

  # Add the entity key to each item to be able to refer to it and update it on the front-end
  for entity in entities:
    entity['_key'] = entity.key.id

  return entities

def update_entity(key: int, updatedItem: APIModel):
  with datastore_client.transaction():
    entity_key = datastore_client.key(APIModel.__name__, key)
    entity = datastore_client.get(entity_key)
    entity.update(updatedItem)

    datastore_client.put(entity)



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

def upload_file(blob_destination_name: str, upload_file: UploadFile):
  storage_client = storage.Client()

  bucket_name = 'proyecto-inicial-storage'
  bucket = storage_client.get_bucket(bucket_name)

  blob = bucket.blob(blob_destination_name)

  blob.upload_from_file(
    file_obj = upload_file.file,
    content_type = upload_file.content_type
  )

  blob.make_public()

  print('URL', blob.public_url)

  return blob.public_url


def is_value_in_object(value: str, object: dict[str, any]):
  values = list(dict.values(object))

  if len(values) == 0:
    return False

  for item in values:
    if value.lower() in str(item).lower():
      return True

  return False
