from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.utils import cors_configuration, FormData, create_and_store_entity, get_all_entities


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


@app.post('/api/send-data/')
def send_data(item: FormData):
  create_and_store_entity(item)

  return item

@app.get('/api/get-all-data/')
def get_all_data():
  result = get_all_entities()

  return result
