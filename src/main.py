from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import Response, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from src.utils import cors_configuration, APIModel, create_and_store_entity, get_all_entities, update_entity, upload_file, insert_data_in_bigquery_table, store_entities_from_csv
import time


app = FastAPI()

# Not working
# origins = [
#   'https://proyecto-inicial-frontend-agk6kyxhfa-no.a.run.app/',
# ]

app.add_middleware(
  CORSMiddleware,
  allow_origins=['*'],
  # allow_origins=origins,
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)


bucket_name = 'artifacts.proyecto-inicial-daniel.appspot.com'
cors_configuration(bucket_name)


# For testing purposes
@app.get('/', response_class=HTMLResponse)
def root():
  return '<!DOCTYPE html>\n<meta name="color-scheme" content="dark">'

@app.post('/api/send-data/')
def send_data(photo_file: UploadFile, creation_date = Form(), name = Form(), dni = Form(), birth_date = Form()):
  item = APIModel(creation_date=creation_date, name=name, dni=dni, birth_date=birth_date)

  if photo_file.size != 0:
    file_url = upload_file(f'photos/{time.time()}-{photo_file.filename}', photo_file)
    item.photo_url = file_url

  entity = create_and_store_entity(item)

  insert_data_in_bigquery_table([entity], [item])

  return item

@app.post('/api/send-data-csv/')
def send_data_csv(csv_file: UploadFile):
  (entities, data) = (None, None)

  try:
    (entities, data) = store_entities_from_csv(csv_file)
  except Exception as reason:
    print(reason)

    return Response(status_code=400)

  insert_data_in_bigquery_table(entities, data)

  return

@app.get('/api/get-all-data/')
def get_all_data(filter: str | None = None):
  result = get_all_entities(filter)

  return result

@app.post('/api/edit-data/{entity_key}', response_class = Response)
def edit_data(entity_key: int, photo_file: UploadFile, creation_date = Form(), name = Form(), dni = Form(), birth_date = Form()):
  updated_item = APIModel(creation_date=creation_date, name=name, dni=dni, birth_date=birth_date)

  if photo_file.size != 0:
    file_url = upload_file(f'photos/{time.time()}-{photo_file.filename}', photo_file)
    updated_item.photo_url = file_url

  update_entity(entity_key, updated_item)

  insert_data_in_bigquery_table([entity_key], [updated_item])

  return
