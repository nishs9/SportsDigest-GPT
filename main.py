import util_functions as util
import sports_digest_gpt_core_functions as sd_gpt
import logging

def get_game_info(event, context):
    logging.basicConfig(filename=f"logs/game_retrieval_logs_{context.event_id}", level=logging.INFO)
    logging.info(f"Game Info Retrieval Job triggered at {context.timestamp} with event id: {context.event_id}")
    try:
        db = util.initialize_firebase(app_context=event["app_context"])
        sd_gpt.game_info_retrieval_job(db)
        logging.info("Job executed successfully.")
    except Exception as e:
        logging.exception("An error occurred: ")

def send_game_summaries(event, context):
    logging.basicConfig(filename=f"logs/game_summary_generator_logs_{context.event_id}", level=logging.INFO)
    logging.info(f"Summary Email Generator and Sender Job triggered at {context.timestamp} with event id: {context.event_id}")
    try:
        db = util.initialize_firebase(app_context=event["app_context"])
        sd_gpt.summary_generator_sender_job(db)
        logging.info("Job executed successfully.")
    except Exception as e:
        logging.exception("An error occurred: ")