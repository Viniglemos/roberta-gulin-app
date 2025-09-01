# Roberta Gulin App

This repository contains the code for a cross‑platform mobile application and its
supporting backend, built as a learning project for an aspiring cloud
engineer. The app is designed for photographer **Roberta Gulin**, providing a
gallery of her work, payment processing, client notifications, calendar
integration with Notion, and a simple menu to showcase different types of
sessions.

## Project structure

```
roberta_app/
├── backend/         # Flask API server (Python)
│   └── app.py       # Main application entry point
├── mobile/          # Kivy mobile front‑end (Python)
│   ├── main.py      # Kivy app entry point (to be implemented)
│   └── …
└── README.md        # This file
```

### Backend

The backend is a Flask application (`backend/app.py`) that performs the
following tasks:

* **Gallery management:** List images stored in an S3 bucket and upload new
  images via a REST endpoint.
* **Payments:** Create payment intents using Stripe (or another payment
  provider). This is optional and can be disabled if not configured.
* **Notifications:** Send notifications via AWS SNS to either a topic or a
  phone number.
* **Calendar integration:** Query a Notion database for upcoming events and
  return them to the mobile app.

Configuration is provided entirely through environment variables. At a minimum,
set the following before running the server:

| Variable             | Description                                                 |
|----------------------|-------------------------------------------------------------|
| `S3_BUCKET_NAME`     | Name of the S3 bucket to store and retrieve images          |
| `AWS_REGION`         | AWS region (default: `us-east-1`)                           |
| `NOTION_TOKEN`       | Internal integration token from Notion                      |
| `NOTION_DATABASE_ID` | ID of the Notion database containing calendar events        |
| `STRIPE_SECRET_KEY`  | Secret key for Stripe (optional, for payments)              |

 backend locally:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install flask boto3 stripe requests
export S3_BUCKET_NAME=your-s3-bucket
export NOTION_TOKEN=secret_notion_token
export NOTION_DATABASE_ID=your_db_id
export AWS_REGION=ap-southeast-2  # Example region (Sydney)
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
python app.py
```


### Mobile application

The mobile front‑end will be built with **Kivy**, a Python framework for
cross‑platform apps. The entry point (`mobile/main.py`) will define the
application layout and interact with the backend through HTTP requests.
Implementation of the mobile app will be added incrementally in the
`mobile/` directory.

To run the Kivy app locally (after implementation):

```bash
cd mobile
python main.py
```


### Version control

All code in this repository should be committed to Git and pushed to a
GitHub repository. Once you are ready to create a repo, initialize Git in
the `roberta_app/` directory, add the files, commit them, and push to GitHub.
The backend and mobile code are kept separate so they can be developed and
deployed independently.

### Next steps

1. Ensure your AWS credentials and Notion integration token are set up. Refer
   to the comments in `backend/app.py` and the environment variables table
   above for guidance.
2. Initialize a Git repository and push the code to GitHub.
3. Implement the Kivy front‑end in `mobile/main.py`, starting with the
   application’s navigation and gallery. Use HTTP requests to interact with
   the backend endpoints defined in `backend/app.py`.
4. Deploy the backend to an EC2 instance and configure an S3 bucket,
   payment provider, and SNS topics/phone numbers as needed.

