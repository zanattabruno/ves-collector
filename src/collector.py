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
    Main page of the Flask app.

    Returns:
        str: "OK" with HTTP status code 200.
    """
    logger.info("Accessed main page.")
    return "OK", 200

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
    return "Error occurred", 500

@app.route("/eventListener/v5", methods=["POST"])
def receive_event():
    """
    Endpoint for receiving a single event.

    Returns:
        str: "OK" with HTTP status code 200 if successful, "ERROR" with HTTP status code 500 if unsuccessful.
    """
    logger.info("Received event at /eventListener/v5")
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
    
@app.route("/eventListener/v5/eventBatch", methods=["POST"])
def receive_event_batch():
    """
    Endpoint for receiving a batch of events.

    Returns:
        str: "OK" with HTTP status code 200 if successful, "ERROR" with HTTP status code 500 if unsuccessful.
    """
    logger.info("Received event batch at /eventListener/v5/eventBatch")
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
    jobj = json.loads(body)
    if 'commonEventHeader' in jobj['event']:
        # store each domain information in individual topic
        topic = jobj['event']['commonEventHeader']['domain'].lower()
        logger.info('Got an event request for {} domain'.format(topic))
        if (len(topic) == 0):
            topic = config['kafka']['default_topic']

        logger.debug('Kafka broker ={} and kafka topic={}'.format(config['kafka']['host'], topic))
        produce_events_in_kafka(jobj, topic)


def produce_events_in_kafka(jobj, topic):
    """
    Produce events in Kafka.

    Args:
        jobj (dict): Dictionary representing the event.
        topic (str): Name of the Kafka topic.

    Raises:
        Exception: If there is an error while posting the event into Kafka.
    """
    try:
        producer = KafkaProducer(bootstrap_servers=[config['kafka']['host']],
                                    value_serializer=lambda x:
                                    dumps(x).encode('utf-8'))
        producer.send(topic, value=jobj)
        logger.debug('Event has been successfully posted into kafka bus')
    except Exception as e:
        logger.error('Getting error while posting event into kafka bus {0}'.format(e))
    
if __name__ == "__main__":
    logger.info("Starting the Flask app.")
    app.run(
        host=config['server']['host'], 
        port=config['server']['port'], 
        debug=config['server']['debug']
    )