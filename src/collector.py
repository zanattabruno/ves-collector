from flask import Flask, request
from kafka import KafkaProducer
from json import dumps
import yaml
import logging
import json

app = Flask(__name__)

def load_config():
    """
    Load configuration from a YAML file.

    Returns:
        dict: Configuration values.
    """
    with open("config/config.yaml", "r") as yamlfile:
        return yaml.safe_load(yamlfile)

config = load_config()

# Set up logging using config value
level = getattr(logging, config['logging']['level'].upper())
logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route("/", methods=["GET"])
def main_page():
    """
    Main page of the ves-collector app.

    Returns:
        str: "OK" with HTTP status code 200.
    """
    logger.info("Accessed main page.")
    version = "1.0.0"
    return f"VES-COLLECTOR - OK - Version {version}", 200

@app.route("/healthz", methods=["GET"])
def healthz():
    """
    Endpoint for checking the health of the application.
    Returns "OK" with a 200 status code if the application is running.
    """
    try:
        logger.info("Accessed healthz page.")
        return "OK", 200
    except Exception as e:
        logger.error(f"Error accessing healthz page: {e}")
        return "Internal Server Error", 500

@app.route("/error", methods=["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
def error_html():
    """
    Error endpoint of the Flask app.

    Returns:
        str: "Error occurred" with HTTP status code 500.
    """
    logger.warning("Error endpoint accessed.")
    error_details = {
        "error": "An error occurred while processing the request.",
        "status_code": 500,
        "request_method": request.method,
        "request_url": request.url,
        "request_data": request.data.decode('utf-8')
    }
    return json.dumps(error_details), 500

@app.route(f"/eventListener/{config['ves']['api_version']}", methods=["POST"])
def receive_event():
    """
    Endpoint for receiving a single event.

    Returns:
        str: "OK" with HTTP status code 200 if successful, "ERROR" with HTTP status code 500 if unsuccessful.
    """
    logger.info(f"Received event at /eventListener/{config['ves']['api_version']}")
    try:
        body = request.get_data().decode('utf-8')
        decoded_body = json.loads(body)
        logger.debug('Decoded body:\n%s', json.dumps(decoded_body, indent=4))
        if 'eventList' in decoded_body:
            events = decoded_body['eventList']            
        elif decoded_body.get('event'):  
            events = [decoded_body['event']]
        else:
            logger.error("JSON body does not contain 'event' or 'eventList'")
            raise ValueError("JSON body does not contain 'event' or 'eventList'")      
        for event in events:
            save_body = {}
            save_body['event'] = event
            logger.debug('Event body:\n%s', json.dumps(save_body, indent=4))
            save_event_in_kafka(json.dumps(save_body))
        return "OK", 200
    except Exception as e:
        logger.error('Getting error while posting event into kafka bus {0}'.format(e))
        return "ERROR", 500
    
@app.route(f"/eventListener/{config['ves']['api_version']}/eventBatch", methods=["POST"])
def receive_event_batch():
    """
    Endpoint for receiving a batch of events.

    Returns:
        str: "OK" with HTTP status code 200 if successful, "ERROR" with HTTP status code 500 if unsuccessful.
    """
    logger.info(f"Received event batch at /eventListener/{config['ves']['api_version']}/eventBatch")
    try:
        body = request.get_data().decode('utf-8')
        decoded_body = json.loads(body)
        logger.debug('Decoded body:\n%s', json.dumps(decoded_body, indent=4))
        if 'eventList' in decoded_body:
            events = decoded_body['eventList']
        elif decoded_body.get('event'): 
            events = [decoded_body['event']]
        else:
            logger.error("JSON body does not contain 'event' or 'eventList'")
            raise ValueError("JSON body does not contain 'event' or 'eventList'")      
        for event in events:
            save_body = {}
            save_body['event'] = event
            logger.debug('Event body:\n%s', json.dumps(save_body, indent=4))
            save_event_in_kafka(json.dumps(save_body))
        return "OK", 200
    except Exception as e:
        logger.error('Getting error while posting event into kafka bus {0}'.format(e))
        return "ERROR", 500

def save_event_in_kafka(body):
    """
    Save an event in Kafka.

    Args:
        body (str): JSON string representing the event.

    Raises:
        ValueError: If the JSON body does not contain 'event' or 'eventList'.
    """
    try:
        jobj = json.loads(body)
        event = jobj.get('event')
        if not event:
            raise ValueError("JSON body does not contain 'event'")

        common_header = event.get('commonEventHeader')
        if not common_header:
            raise ValueError("JSON body does not contain 'commonEventHeader'")

        domain = common_header.get('domain', '').lower()
        if not domain:
            topic = config['kafka']['default_topic']
        else:
            topic = domain

        # Extract headers
        source_name = common_header.get('sourceName')
        headers = []
        if source_name:
            headers.append(('sourceName', source_name.encode('utf-8')))

        logger.info(f"Got an event request for {topic} domain")
        logger.debug(f"Kafka broker={config['kafka']['host']} and kafka topic={topic}")
        produce_events_in_kafka(jobj, topic, headers)
    except Exception as e:
        logger.error(f"Error while saving event in Kafka: {e}")


def produce_events_in_kafka(jobj, topic, headers=None):
    """
    Produce events in Kafka.

    Args:
        jobj (dict): Dictionary representing the event.
        topic (str): Name of the Kafka topic.
        headers (list[tuple]): List of tuples representing headers.

    Raises:
        Exception: If there is an error while posting the event into Kafka.
    """
    try:
        producer = KafkaProducer(
            bootstrap_servers=[config['kafka']['host']],
            value_serializer=lambda x: dumps(x).encode('utf-8')
        )
        producer.send(topic, value=jobj, headers=headers)
        logger.debug('Event has been successfully posted into kafka bus')
    except Exception as e:
        logger.error(f'Error while posting event into kafka bus: {e}')
        raise
    
if __name__ == "__main__":
    try:
        logger.info("Starting the ves-collector app.")
        app.run(
            host=config['server']['host'], 
            port=config['server']['port'], 
            debug=config['server']['debug']        )

    except Exception as e:
        logger.error(f"Error starting the ves-collector app: {e}")
