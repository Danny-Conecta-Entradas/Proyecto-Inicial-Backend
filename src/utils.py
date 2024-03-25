from pydantic import BaseModel
from google.cloud import storage, datastore
# from google.cloud.datastore.query import PropertyFilter


class APIModel(BaseModel):
  creation_date: str
  name: str
  dni: str
  birth_date: str

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

def is_value_in_object(value: str, object: dict[str, any]):
  values = list(dict.values(object))

  if len(values) == 0:
    return False

  for item in values:
    if value.lower() in str(item).lower():
      return True

  return False
