import requests
import json
import logging

from config import Config

config = Config()

logger = logging.getLogger(__name__)

def wake_up_myself():
    logger.info('wake_up_myself')
    url = config.MYSELF_URL
    try:
        conn = requests.get(url)
    except Exception as e:
        logger.error(str(e), exc_info=True)


def reurl(token,origin_url):
    reurl_headers = {
        "Content-Type" : "application/json" ,
        "reurl-api-key" : token 
    }
    payload = {"url": origin_url}
    payload_json = json.dumps(payload)

    r = requests.post("https://api.reurl.cc/shorten",headers = reurl_headers,data = payload_json)
    try:
        response_json = json.loads(r.text)
    
        if 'res' in response_json:
            return response_json['short_url']
        elif 'code' in response_json :
            return 'fail'
    except json.decoder.JSONDecodeError:
        return r.text
