from fastapi import FastAPI
from google.cloud import datastore
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
  'https://proyecto-inicial-agk6kyxhfa-no.a.run.app/',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database_name = 'registro'
datastore_client = datastore.Client(database = database_name)


class FormData(BaseModel):
  timestamp: str
  string_qr: str


@app.post('/api/send-data/')
def send_data(item: FormData):
  create_and_store_entity(item)

  return item


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
