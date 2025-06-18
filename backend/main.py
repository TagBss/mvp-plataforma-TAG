from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import shutil

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://dashboard-nextjs-and-fastapi.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/chart-data")
def get_chart_data():
    df = pd.read_excel("dados.xlsx")
    return df.to_dict(orient="records")

@app.post("/upload")
def upload_excel(file: UploadFile = File(...)):
    with open("dados.xlsx", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "status": "uploaded"}