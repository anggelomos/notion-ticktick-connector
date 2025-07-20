import logging
import os
from src.s3_client import S3Client
from src.task_syncer import TaskSyncer

from tickthon import TicktickClient, TicktickListIds
from nothion import NotionClient

# Load environment variables from .env file only in development
if os.getenv("ENVIRONMENT") == "dev" or os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)")

connection_filename = os.getenv("CONNECTION_DATA_FILENAME")
s3_client = S3Client("bulloh-plotter")
connection_data = s3_client.download_connection_file(connection_filename)
notion_tasks_db_id="19541ab983668171baf0d28b0afd4d36"
ticktick_list_ids = TicktickListIds(INBOX="inbox114478622",
                                    TODAY_BACKLOG="6616e1af8f08b66b69c7a5c5",
                                    WEEK_BACKLOG="61c62f198f08c92d0584f678",
                                    MONTH_BACKLOG="61c634f58f08c92d058540ba",
                                    WEIGHT_MEASUREMENTS="640c03cd8f08d5a6c4bb32e7")

def main():
    ticktick = TicktickClient(os.getenv("TT_USER"),
                              os.getenv("TT_PASS"),
                              ticktick_list_ids,
                              api_token=connection_data.ticktick_data.token,
                              cookies=connection_data.ticktick_data.cookies
                              )
    connection_data.ticktick_data.token = ticktick.ticktick_api.auth_token
    connection_data.ticktick_data.cookies = ticktick.ticktick_api.cookies
    s3_client.upload_connection_file(connection_data, connection_filename)
    notion = NotionClient(os.getenv("NT_AUTH"), notion_tasks_db_id)

    task_syncer = TaskSyncer(ticktick, notion)
    task_syncer.sync_tasks()


if __name__ == "__main__":
    main()
