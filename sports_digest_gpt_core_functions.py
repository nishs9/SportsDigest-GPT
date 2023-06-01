import requests
import util_functions as util
import pandas as pd
import openai
import secret_keys
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

####################################################################################################################################################
# SportsDigest-GPT Core Jobs #

# Function that saves the day's upcoming games to the database
def game_info_retrieval_job(db):
    save_upcoming_game_info(db)

# Function that generates game summaries from boxscores and 
# sends them as an email blast
def summary_generator_sender_job(db):
    game_ids = get_unsummarized_games(db)
    for game in game_ids:
        get_single_game_boxscore_data(db, game)
    generate_all_game_summaries(db)
    send_summary_email(db)

####################################################################################################################################################
# SportsDigest-GPT Sub-Jobs #

# Retrieves information about all of today's games and saves it to the database
def save_upcoming_game_info(db):
    url = "http://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
    response = requests.get(url)
    data = response.json()

    for game in data['events']:
        print("Processing game: " + game['shortName'] + "...")
        game_short_name = game['shortName'].split(' @ ')
        unique_game_id = game['id'] + "-" + game_short_name[0] + "-" + game_short_name[1]

        game_data = {
            'home_team': game['competitions'][0]['competitors'][0]['team']['displayName'],
            'home_team_id': game['competitions'][0]['competitors'][0]['team']['id'],
            'away_team': game['competitions'][0]['competitors'][1]['team']['displayName'],
            'away_team_id': game['competitions'][0]['competitors'][1]['team']['id'],
            'short_detail': game['status']['type']['shortDetail'],
            'is_summarized': False,
        }

        doc_ref = db.collection('games').document(unique_game_id)
        doc_ref.set(game_data)

# Retrieves and returns a list of all games that have not yet been summarized 
def get_unsummarized_games(db):
    print("Retrieving unsummarized games...")
    game_ids = []
    games_to_summarize = db.collection('games').where('is_summarized', '==', False).stream()

    for game in games_to_summarize:
        curr_dict = {
            "game_id": game.id, 
            "home_team_id": game.to_dict()["home_team_id"], 
            "away_team_id": game.to_dict()["away_team_id"]
        }
        game_ids.append(curr_dict)

    return game_ids

# Scrape the box score data of a given game and save it to the database
def get_single_game_boxscore_data(db, game_dict):
    print("Scraping box score data for game: " + game_dict['game_id'] + "...")
    game_id = game_dict['game_id'].split('-')[0]

    away_team_full_name = util.get_team_name_by_id(db, game_dict['away_team_id'])
    home_team_full_name = util.get_team_name_by_id(db, game_dict['home_team_id'])

    away_team_abbrev = util.get_team_abbrev_by_id(db, game_dict['away_team_id'])
    home_team_abbrev = util.get_team_abbrev_by_id(db, game_dict['home_team_id'])

    boxscore_header = away_team_full_name + " vs " + home_team_full_name + " Box Score\n\n"

    url = f'https://www.espn.com/mlb/boxscore/_/gameId/{game_id}'

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    tables = soup.find_all('table')

    boxscore_tables = ""
    for i, table in enumerate(tables):
        if i == 0:
            continue
        elif i == 10:
            break

        columns = [th.text for th in table.find('tr').find_all('th')]

        data_rows = table.find_all('tr')[1:]
        data = [[td.text for td in row.find_all('td')] for row in data_rows]

        df = pd.DataFrame(data, columns=columns)

        #TODO: Remove writing to file once we are ready to deploy
        with open("test_files/test.txt", 'a') as f:
            f.write(df.to_string())
            f.write('\n\n')

        boxscore_tables += df.to_string(index=False) + "\n\n"

    boxscore_data = {
            'home_team': home_team_full_name,
            'home_team_id': game_dict['home_team_id'],
            'away_team': away_team_full_name,
            'away_team_id': game_dict['away_team_id'],
            'game_ref_id': game_id,
            'boxscore_content': boxscore_header + boxscore_tables,
            'is_summarized': False,
    }

    unique_boxscore_id = game_id + "-" + away_team_abbrev + "-" + home_team_abbrev + "-boxscore"

    doc_ref = db.collection('boxscores').document(unique_boxscore_id)
    doc_ref.set(boxscore_data)

# Generate summaries for all unsummarized games in the database
def generate_all_game_summaries(db):
    boxscores_to_summarize = db.collection('boxscores').where('is_summarized', '==', False).stream()

    for boxscore in boxscores_to_summarize:
        curr_dict = {
            "boxscore_id": boxscore.id, 
            "home_team_id": boxscore.to_dict()["home_team_id"], 
            "away_team_id": boxscore.to_dict()["away_team_id"],
            "game_ref_id": boxscore.to_dict()["game_ref_id"],
            "boxscore_content": boxscore.to_dict()["boxscore_content"]
        }
        generate_single_game_summary(db, curr_dict)

# Generate a summary for a single game with the GPT-3.5 model and save it to the database
def generate_single_game_summary(db, boxscore_dict):
    print("Generating summary for boxscore: " + boxscore_dict['boxscore_id'] + "...")
    away_team = util.get_team_name_by_id(db, boxscore_dict['away_team_id'])
    away_team_abbrev = util.get_team_abbrev_by_id(db, boxscore_dict['away_team_id'])
    home_team = util.get_team_name_by_id(db, boxscore_dict['home_team_id'])
    home_team_abbrev = util.get_team_abbrev_by_id(db, boxscore_dict['home_team_id'])
    prompt = f"Give me a brief summary of a game between the {away_team} and {home_team} from the following box score. Avoid being overly verbose. Just provide a basic summary of the game, and some standout performers:\n\n"

    openai.api_key = secret_keys.openai_api_key

    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
          {"role": "system", "content": "You are a helpful assistant that summarizes MLB boxscores."},
          {"role": "user", "content": prompt + boxscore_dict['boxscore_content']},
      ]
    )
    
    summary = response.choices[0].message['content']

    summary_data = {
        'home_team': home_team,
        'home_team_id': boxscore_dict['home_team_id'],
        'away_team': away_team,
        'away_team_id': boxscore_dict['away_team_id'],
        'game_ref_id': boxscore_dict['game_ref_id'],
        'summary_content': summary,
        'email_sent': False,
        'prompt_tokens': response['usage']['prompt_tokens'],
        'completion_tokens': response['usage']['completion_tokens']
    }
    
    unique_summary_id = boxscore_dict['game_ref_id'] + "-" + away_team_abbrev + "-" + home_team_abbrev + "-summary"

    doc_ref = db.collection('summaries').document(unique_summary_id)
    doc_ref.set(summary_data)

    game_query_id = boxscore_dict['game_ref_id'] + "-" + away_team_abbrev + "-" + home_team_abbrev
    update_summarized_flag(db, 'games', game_query_id)

    boxscore_query_id = boxscore_dict['game_ref_id'] + "-" + away_team_abbrev + "-" + home_team_abbrev + "-boxscore"
    update_summarized_flag(db, 'boxscores', boxscore_query_id)

# Generate the email contents for all summaries that have not been emailed yet along with the game ref ids
def generate_email_contents(db):
    summaries_to_send = db.collection('summaries').where('email_sent', '==', False).stream()
    game_ref_ids = []
    summary_email_sections = []

    for summary in summaries_to_send:
        summary_doc = summary.to_dict()
        game_title = f"{summary_doc['away_team']} vs {summary_doc['home_team']} Game Summary"
        summary_dict = {"game_title": game_title, "game_summary": summary_doc['summary_content']}
        summary_email_sections.append(summary_dict)
        game_ref_ids.append(summary_doc['game_ref_id'])

    return game_ref_ids, summary_email_sections

# Send an email with all the summaries that have not been emailed yet and set the
# email_sent flag to True for the summaries that were sent
def send_summary_email(db):
    game_ref_ids, summary_email_sections = generate_email_contents(db)

    date = datetime.datetime.today().strftime("%A %B %d, %Y")

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    username = secret_keys.from_email
    password = secret_keys.from_email_password
    from_addr = secret_keys.from_email
    to_addrs = [secret_keys.to_email]

    file_loader = FileSystemLoader('.')
    env = Environment(loader=file_loader)
    template = env.get_template('summary_email_template.html')
    
    header = f"Here is a rundown of all the MLB action from {date}:\n\n"

    html = template.render(header=header, sections=summary_email_sections)

    msg = MIMEMultipart("alternative")
    msg['From'] = from_addr
    msg['To'] = ', '.join(to_addrs)
    msg['Subject'] = f'SportsDigest-GPT Summary for {date}'

    html_part = MIMEText(html, 'html')
    msg.attach(html_part)

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(username, password)
    server.sendmail(from_addr, to_addrs, msg.as_string())
    server.quit()

    update_email_sent_flag(db, game_ref_ids)

####################################################################################################################################################
# General helper and debug functions #

# Helper function to update the is_summarized flag for a game or boxscore
# It is called after a summary is generated.
def update_summarized_flag(db, collection, query_id):
    docs_ref = db.collection(collection).where('is_summarized', '==', False).stream()
    for doc in docs_ref:
        doc_id = doc.id
        doc_ref = db.collection(collection).document(doc_id)
        doc_ref.update({'is_summarized': True})

# Helper function to update the email_sent flag for summaries
# It is called after an email is sent.
def update_email_sent_flag(db, game_ref_ids):
    summary_flags_to_update = db.collection('summaries').where('game_ref_id', 'in', game_ref_ids).stream()
    for summary_doc in summary_flags_to_update:
        summary_id = summary_doc.id
        summary_doc_ref = db.collection('summaries').document(summary_id)
        summary_doc_ref.update({'email_sent': True})

# *WARNING** CLEARS ALL DATA FROM THE GAMES, BOXSCORES, AND SUMMARIIES COLLECTIONS
def clear_main_collections():
    db = util.initialize_firebase("local")
    util.clear_collection(db, 'games')
    util.clear_collection(db, 'boxscores')
    util.clear_collection(db, 'summaries')

# Full job flow for testing purposes only
####--- WILL DELETE ALL DATA IN THE DATABASE ---####
def full_test_flow():
    db = util.initialize_firebase("local")
    util.clear_collection(db, 'games')
    util.clear_collection(db, 'boxscores')
    util.clear_collection(db, 'summaries')
    save_upcoming_game_info(db)
    game_ids = get_unsummarized_games(db)
    for game in game_ids:
        get_single_game_boxscore_data(db, game)
    generate_all_game_summaries(db)
    send_summary_email(db)

####################################################################################################################################################

if __name__ == "__main__":
    #full_test_flow()
    #send_summary_email(util.initialize_firebase())
    #clear_main_collections()
    game_info_retrieval_job(util.initialize_firebase("local"), app_context="gcp")
    #summary_generator_sender_job()
    pass
