from fastapi import UploadFile
from pydantic import BaseModel
from google.cloud import storage, datastore, bigquery
from google.cloud.bigquery import SchemaField
import csv
import time
import datetime
import math
import io


class APIModel(BaseModel):
  creation_date: int
  name: str
  dni: str
  birth_date: int | str
  photo_url: str | None = None


def get_datastore_client():
  database_name = 'registro'
  datastore_client = datastore.Client(database = database_name)

  return datastore_client


def create_entity(form_data: APIModel):
  datastore_client = get_datastore_client()

  kind = APIModel.__name__
  form_key = datastore_client.key(kind)

  form_data.birth_date = int(form_data.birth_date)

  entity = datastore.Entity(key = form_key)
  entity.update(form_data)

  return entity

def store_entity(entity: datastore.Entity):
  datastore_client = get_datastore_client()
  datastore_client.put(entity)

def create_and_store_entity(form_data: APIModel):
  entity = create_entity(form_data)
  store_entity(entity)

  return entity

def create_multiple_entities(data: list[APIModel]) -> list[datastore.Entity]:
  entities = []

  for item in data:
    entity = create_entity(item)
    entities.append(entity)

  return entities

def store_multiple_entities(entities: list[datastore.Entity]):
  datastore_client = get_datastore_client()
  datastore_client.put_multi(entities)

def create_and_store_multiple_entities(data: list[APIModel]):
  entities = create_multiple_entities(data)
  store_multiple_entities(entities)

  return entities

def get_all_entities(filterValue: str | None = None):
  datastore_client = get_datastore_client()

  query = datastore_client.query(kind = APIModel.__name__)
  query.order = ['-creation_date']

  entities: list[APIModel] = list(query.fetch())

  if filterValue != None:
    entities = list(
      filter(
        lambda object: is_value_in_object(filterValue, object, ['creation_date', 'birth_date', 'photo_url']),
        entities
      )
    )

  # Add the entity key to each item to be able to refer to it and update it on the front-end
  for entity in entities:
    entity['_key'] = entity.key.id

  return entities

def update_entity(key: int, updatedItem: APIModel):
  datastore_client = get_datastore_client()

  with datastore_client.transaction():
    entity_key = datastore_client.key(APIModel.__name__, key)
    entity = datastore_client.get(entity_key)
    entity.update(updatedItem)

    datastore_client.put(entity)

def store_entities_from_csv(csv_file: UploadFile):
  # Transform the binary file into a text file for the csv reader
  text_file = io.TextIOWrapper(csv_file.file, encoding='utf-8')

  reader = csv.DictReader(text_file, delimiter=',')

  data: list[APIModel] = []

  for row in reader:
    creation_date = get_current_date_in_miliseconds()
    item = APIModel(creation_date=creation_date, **row)

    # If the date is in `string` format (e.g. comes from a CSV)
    # then transform it into `int` value
    if type(item.birth_date) == str:
      item.birth_date = get_formatted_date_as_miliseconds(item.birth_date, '%Y-%m-%d')

    data.append(item)

    print(item)

  entities = create_and_store_multiple_entities(data)

  return (entities, data)


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


def is_value_in_object(value: str, object: dict[str, any], ignore_keys: list[str] | None = None):
  key_value_pairs = list(dict.items(object))

  for key, item in key_value_pairs:
    if ignore_keys != None and key in ignore_keys:
      continue

    if value.lower() in str(item).lower():
      return True

  return False

def get_bigquery_dataset():
  bigquery_client = bigquery.Client()

  dataset_name = 'proyecto_inicial_dataset'
  dataset = None

  try:
    dataset = bigquery_client.get_dataset(dataset_name)
  except:
    dataset = bigquery_client.create_dataset(dataset_name)

  return dataset

def get_bigquery_table():
  bigquery_client = bigquery.Client()

  dataset = get_bigquery_dataset()

  table_name = f'{dataset.dataset_id}.proyecto-inicial-table'

  table = None

  try:
    table = bigquery_client.get_table(table_name)
  except:
    table = bigquery_client.create_table(table_name)
    table.schema = [
      # https://cloud.google.com/bigquery/docs/reference/rest/v2/tables#TableFieldSchema.FIELDS.mode
      SchemaField('_key', 'INTEGER', mode='REQUIRED'),
      SchemaField('creation_date', 'INTEGER', mode='REQUIRED'),
      SchemaField('name', 'STRING', mode='REQUIRED'),
      SchemaField('dni', 'STRING', mode='REQUIRED'),
      SchemaField('birth_date', 'INTEGER', mode='REQUIRED'),
      SchemaField('photo_url', 'STRING', mode='REQUIRED'),
    ]

    table = bigquery_client.update_table(table, ['schema'])

    # Add a small delay to avoid `NOT_FOUND Table` error when inserting data after creating the table
    time.sleep(1)

  return table

def insert_data_in_bigquery_table(entities_or_entities_id: list[datastore.Entity] | list[int], data: list[APIModel]):
  bigquery_client = bigquery.Client()
  table = get_bigquery_table()

  data_dump_list = []

  for index, item in enumerate(data):
    entity_or_entity_id = entities_or_entities_id[index]

    data_dump = item.model_dump()

    if type(entity_or_entity_id) is int:
      data_dump['_key'] = entity_or_entity_id
    else:
      data_dump['_key'] = entity_or_entity_id.key.id

    data_dump_list.append(data_dump)

  bigquery_client.insert_rows_json(table, data_dump_list)

# Get current date in miliseconds to match JavaScript `Date.now()` format
def get_current_date_in_miliseconds():
  return math.floor(time.time() * 1000)

def get_formatted_date_as_miliseconds(string_date: str, format: str):
  datetime_object = datetime.datetime.strptime(string_date, format)
  date_int =  math.floor(datetime_object.timestamp() * 1000)

  return date_int
