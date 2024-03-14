from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils import cors_configuration, create_and_store_entity, FormData


app = FastAPI()

origins = [
  'https://proyecto-inicial-backend-agk6kyxhfa-uc.a.run.app',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    # allow_methods=["*"],
    allow_headers=["*"],
)


bucket_name = 'artifacts.proyecto-inicial-daniel.appspot.com'
cors_configuration(bucket_name)


@app.post('/api/send-data/')
def send_data(item: FormData):
  create_and_store_entity(item)

  return item
