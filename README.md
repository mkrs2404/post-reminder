# Notion Content Deadline Reminder

This script checks a Notion database for pages representing content (like blog posts) and sends reminders to a Slack channel when specific deadlines (first draft, ready by, publishing date) are approaching (specifically, the next day).

## Features

- Connects to a specified Notion database.
- Reads pages and checks predefined date properties.
- Identifies pages where a deadline is one day away.
- Sends a notification message to a specified Slack channel, mentioning the author (based on the Notion 'Person' property) and the content title.
- Uses environment variables for secure configuration.
- Logs its operations for monitoring.

## Setup

### Prerequisites

- Python 3.x
- Access to a Notion workspace and a Slack workspace.

### Installation

1.  **Clone the repository (optional):**
    If you haven't already, get the code:
    ```bash
    git clone <repository-url>
    cd post-reminder
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    - Create a `.env` file in the project root directory by copying the example:
      ```bash
      cp .env.example .env
      ```
    - Edit the `.env` file and add your specific credentials:
      - `NOTION_TOKEN`: Your Notion integration token. See [Notion's documentation](https://developers.notion.com/docs/getting-started#step-1-create-an-integration) on creating integrations. Ensure the integration has read access to the database.
      - `NOTION_DATABASE_ID`: The ID of the Notion database you want to monitor. You can find this in the URL of your database (`https://www.notion.so/your-workspace/DATABASE_ID?v=...`).
      - `SLACK_BOT_TOKEN`: Your Slack bot token (usually starts with `xoxb-`). See [Slack API documentation](https://api.slack.com/authentication/basics#bot-tokens) for creating a bot and getting a token. The bot needs the `chat:write` permission.
      - `SLACK_CHANNEL_ID`: The ID of the Slack channel where reminders should be posted. You can find this in the channel's URL in Slack or via other methods. Ensure the bot is added to this channel.

### Notion Database Setup

Ensure your Notion database has the following properties:

- A **Title** property (default name 'title' is assumed by the script, but can be configured).
- A **Person** property to assign authors (default name 'author' is assumed).
- Three **Date** properties for tracking deadlines (default names assumed):
    - `first_draft_date`
    - `ready_by_date`
    - `publishing_date`

*Note: You can change the assumed property names by modifying the constants at the top of `src/main.py`.*

## Usage

Run the script from the project's root directory:

```bash
python3 main.py