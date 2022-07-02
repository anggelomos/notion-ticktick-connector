import json
from main import main


def lambda_handler(event, conntext):
    main()

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With',
            'Access-Control-Allow-Origin': 'https://upbeat-jackson-774e87.netlify.app',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps('Tasks synced!')
    }
