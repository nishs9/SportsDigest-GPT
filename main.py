import util_functions as util
import sports_digest_gpt_core_functions as sd_gpt

def get_game_info(event, context):
    print(f"Game Info Retrieval Job triggered at {context.timestamp} with event id: {context.event_id}")
    try:
        db = util.initialize_firebase(app_context=event["app_context"])
        sd_gpt.game_info_retrieval_job(db)
        print("Job executed successfully.")
    except Exception as e:
        util.error_handler(e)

def send_game_summaries(event, context):
    print(f"Summary Email Generator and Sender Job triggered at {context.timestamp} with event id: {context.event_id}")
    try:
        db = util.initialize_firebase(app_context=event["app_context"])
        sd_gpt.summary_generator_sender_job(db)
        print("Job executed successfully.")
    except Exception as e:
        util.error_handler(e)