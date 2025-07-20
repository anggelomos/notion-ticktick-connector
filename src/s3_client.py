import json
import logging
from attr import asdict, define
import boto3
import botocore
import cattrs


@define
class HealthConnectData:
    token: str | None = None
    refresh_token: str | None = None


@define
class TicktickData:
    token: str | None = None
    cookies: dict[str, str] | None = None


@define
class ConnectionData:
    health_connect_data: HealthConnectData
    ticktick_data: TicktickData


class S3Client:

    BASE_FILE_NAME = "bulloh_stats"

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.s3 = boto3.client("s3")

    def upload_connection_file(self, file_content: ConnectionData, filename: str):
        self.s3.put_object(Bucket=self.bucket_name,
                           Key=f"{filename}.json",
                           Body=json.dumps(asdict(file_content)))

    def download_connection_file(self, filename: str) -> ConnectionData:
        """Downloads a connection data file from S3 and converts it to a StorageFile object.

        Args:
            filename (str): The filename to download (not date-based).

        Returns:
            StorageFile: The StorageFile object.
        """
        converter = cattrs.Converter()
        converter.register_structure_hook(HealthConnectData, lambda d, _: HealthConnectData(**d))
        converter.register_structure_hook(TicktickData, lambda d, _: TicktickData(**d))

        file_data = self._try_get_connection_file(filename, converter)
        if file_data is not None:
            return file_data

        raise FileNotFoundError(f"Connection data file '{filename}' not found in S3. "
                                "This file is required for the application to function.")

    def _try_get_connection_file(self, filename: str, converter) -> ConnectionData | None:
        """Helper method to try retrieving a connection file.

        Returns:
            ConnectionData or None if file not found.
        """
        try:
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=f"{filename}.json"
            )
            data = json.loads(response["Body"].read().decode("utf-8"))
            return converter.structure(data, ConnectionData)
        except self.s3.exceptions.NoSuchKey:
            logging.info(f"No connection file found: {filename}")
            return None
        except botocore.exceptions.ClientError as e:
            logging.error(f"Error downloading connection file: {e}")
            raise e
