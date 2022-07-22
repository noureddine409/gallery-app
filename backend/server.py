import psycopg2
import boto3

from typing import List

from pydantic import BaseModel

import uvicorn

from fastapi import FastAPI, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(debug=True)
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

access_key = 'AKIARQYK7UVDYO2NEEX4'
secret_access_key = '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'


class VideoModel(BaseModel):
    id : int
    video_title: str
    video_url: str



@app.get('/status')
async def checkStatus():
    return 'hello world'

@app.get('/videos', response_model=List[VideoModel])
async def get_videos():
    formated_videos = []
    try:
        conn = psycopg2.connect(host='localhost', database='video_app_db', user='postgres', password='maroc123')
        cur = conn.cursor()
        print('connecting to database was succesufull')

        cur.execute("SELECT * FROM video ORDER BY id DESC")

        rows = cur.fetchall()
        
        for row in rows:
            formated_videos.append(
                VideoModel(id=row[0], video_title=row[1], video_url=row[2])
            )

        cur.close() 
        conn.close()
        return formated_videos
    except Exception as err:
        print(err)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

@app.post('/videos', status_code=status.HTTP_201_CREATED)
async def upload_video(file: UploadFile):
    # upload file to s3 aws
    s3 = boto3.resource("s3", 
    aws_access_key_id= access_key,aws_secret_access_key = secret_access_key)
    upload_file_bucket = 'mybucketnoureddinelachgar'
    bucket = s3.Bucket(upload_file_bucket)
    bucket.upload_fileobj(file.file, file.filename, ExtraArgs={"ACL": "public-read"})
    uploaded_file_url = f"https://{upload_file_bucket}.s3.amazonaws.com/{file.filename}"

    try:
        conn = psycopg2.connect(host='localhost', database='video_app_db', user='postgres', password='maroc123')
        cur = conn.cursor()
        print('connecting to database was succesufull')

        cur.execute(""" INSERT INTO video(title, url) VALUES(%s, %s) """, (file.filename, uploaded_file_url))
        conn.commit()
        cur.close() 
        conn.close()
    except Exception as err:
        print(err)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return {'data': 'video added'}



if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
