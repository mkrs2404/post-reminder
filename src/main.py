import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from notion_client import Client, APIResponseError
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Constants for Notion property names
NOTION_FIRST_DRAFT_DATE_PROP = 'first_draft_date'
NOTION_READY_BY_DATE_PROP = 'ready_by_date'
NOTION_PUBLISHING_DATE_PROP = 'publishing_date'
NOTION_TITLE_PROP = 'title' # Assuming 'title' is the name of the Title property
NOTION_AUTHOR_PROP = 'author' # Assuming 'author' is the name of the Person property

# Initialize clients
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_CHANNEL_ID = os.getenv('SLACK_CHANNEL_ID')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

if not all([NOTION_TOKEN, SLACK_BOT_TOKEN, SLACK_CHANNEL_ID, NOTION_DATABASE_ID]):
    logging.error("Missing one or more environment variables (NOTION_TOKEN, SLACK_BOT_TOKEN, SLACK_CHANNEL_ID, NOTION_DATABASE_ID).")
    exit(1)

notion = Client(auth=NOTION_TOKEN)
slack_client = WebClient(token=SLACK_BOT_TOKEN)

def check_date_proximity(date_str):
    """Check if a date is within one day of today"""
    if not date_str:
        return False
    date = datetime.strptime(date_str, '%Y-%m-%d')
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    return date.date() == tomorrow.date()

# Note: Slack mentions using '@name' might not work if display names differ or are not unique.
# For reliable mentions, you might need to map Notion users to their Slack User IDs.
def send_slack_message(author_mention, title, stage):
    """Send a message to Slack"""
    try:
        # Use the author_mention directly (could be name or ID)
        message = f"{author_mention} - Your post '{title}', has the {stage} date coming up tomorrow - please ensure that your content is ready and reviewed as per the right stage."
        logging.info(f"Sending Slack message to channel {SLACK_CHANNEL_ID} for post '{title}' ({stage})")
        response = slack_client.chat_postMessage(
            channel=SLACK_CHANNEL_ID,
            text=message
        )
    except SlackApiError as e:
        logging.error(f"Error sending Slack message: {e.response['error']}")

def get_page_title(properties):
    """Safely extracts the title from page properties."""
    title_prop = properties.get(NOTION_TITLE_PROP, {})
    if title_prop.get('type') == 'title' and title_prop.get('title'):
        return title_prop['title'][0].get('plain_text', 'Untitled')
    return 'Untitled'

def get_page_author_mention(properties):
    """Safely extracts the author's name or prepares a mention string."""
    # This assumes the 'author' property is a 'people' type.
    # You might need to adjust this based on your Notion setup.
    # Ideally, map Notion user ID/email to Slack user ID for reliable mentions <@U123ABC>.
    author_prop = properties.get(NOTION_AUTHOR_PROP, {})
    if author_prop.get('type') == 'people' and author_prop.get('people'):
        # Using name for now, but Slack ID is preferred.
        return author_prop['people'][0].get('name', 'Unknown Author') 
    return 'Unknown Author'

def get_date_property(properties, prop_name):
    """Safely extracts a date property."""
    date_prop = properties.get(prop_name, {})
    if date_prop.get('type') == 'date' and date_prop.get('date'):
        return date_prop['date'].get('start')
    return None

def main():
    logging.info("Starting Notion content reminder script.")
    try:
        # Query the Notion database
        logging.info(f"Querying Notion database: {NOTION_DATABASE_ID}")
        response = notion.databases.query(database_id=NOTION_DATABASE_ID)
        
        processed_pages = 0
        notifications_sent = 0
        for page in response.get('results', []):
            processed_pages += 1
            properties = page.get('properties', {})
            page_id = page.get('id')
            
            # Extract details safely
            title = get_page_title(properties)
            # For Slack mentions, ideally map Notion user to Slack ID (<@Uxxxx>)
            # For now, using the name from Notion.
            author_mention = get_page_author_mention(properties) 
            
            dates_to_check = {
                "first draft": get_date_property(properties, NOTION_FIRST_DRAFT_DATE_PROP),
                "final draft": get_date_property(properties, NOTION_READY_BY_DATE_PROP),
                "published version": get_date_property(properties, NOTION_PUBLISHING_DATE_PROP)
            }
            
            logging.debug(f"Checking page: {title} (ID: {page_id}), Author: {author_mention}, Dates: {dates_to_check}")

            # Check each date and send notifications
            for stage, date_str in dates_to_check.items():
                if check_date_proximity(date_str):
                    logging.info(f"Deadline approaching for '{title}' ({stage}) on {date_str}. Notifying {author_mention}.")
                    send_slack_message(author_mention, title, stage)
                    notifications_sent += 1

        logging.info(f"Script finished. Processed {processed_pages} pages. Sent {notifications_sent} notifications.")

    except APIResponseError as e:
        logging.error(f"Notion API Error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()