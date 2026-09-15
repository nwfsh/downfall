from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


from bronze_youtube_ingest_creator_videos import get_video_ids_for_creator, land_video_links # added another to store 
from bronze_youtube_ingest_comments import ingest_video


CALIBRATION_SET = [
    {"label": "James Charles",  "channel_id": "UCucot-Zp428OwkyRm2I7v2Q", "start_date": "2019-05-01", "end_date": "2019-06-15"},
    {"label": "PewDiePie",      "channel_id": "UC-lHJZR3Gqxm24_Vd_AJ5Yw", "start_date": "2017-02-01", "end_date": "2017-03-05"},
    {"label": "Logan Paul",     "channel_id": "UCG8rbF3g2AMX70yOd8vqIZg", "start_date": "2017-12-15", "end_date": "2018-02-10"},
    {"label": "Stephanie Soo",  "channel_id": "UCo9ZZ04kIhN_8xGxvnjaduQ", "start_date": "2019-12-10", "end_date": "2020-01-31"},
    {"label": "Trisha Paytas",  "channel_id": "UCF2oW5-MO8dB6ul9WH9xi0A", "start_date": "2021-05-25", "end_date": "2021-07-05"},
    {"label": "Ryan Higa",      "channel_id": "UCSAUGyc_xA8uYzaIVG6MESQ", "start_date": "2019-05-01", "end_date": "2019-06-30"},
]


def pull_creator_videos():
    video_ids = []

    for creator in CALIBRATION_SET:
        ## return links, flagged, ignore flagged but need to unpack them
        video_id = get_video_ids_for_creator(
            creator["channel_id"], ## will raise error if returns nothing
            creator.get("start_date"), ## allows returning nothing 
            creator.get("end_date") ## get() allows returning nothing
        )

        land_video_links(creator["channel_id"], creator["label"], video_id)
        video_ids.extend(video_id) # append is one object, extend iterates and add all into list
        print(f"total ingested: {len(video_ids)}") #cross check with the amount 
    return video_ids


def pull_comments(**context): ## allows a function to take in multiple parameters 
    ti = context["ti"] ## pull out only the parameters u needed which was the ti 
    video_ids = ti.xcom_pull(task_ids="pull_creator_videos")
    for video_id in video_ids:
        ingest_video(video_id, fetch_full_replies=False)



with DAG(
    dag_id = "youtube_bronze_pipeline",
    start_date = datetime(2026, 9, 13),
    schedule_interval=None, # set manual trigger
    catchup = False,
) as dag:
    pull_videos_task = PythonOperator(
        task_id="pull_creator_videos",
        python_callable=pull_creator_videos,
    )
    pull_comments_task = PythonOperator(
        task_id="pull_comments",
        python_callable=pull_comments,
    )
    pull_videos_task >> pull_comments_task
