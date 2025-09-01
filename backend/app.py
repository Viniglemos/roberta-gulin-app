"""
Flask backend for the Roberta Gulin mobile app.

This backend exposes a simple REST API that integrates with AWS services and
external APIs to support the mobile front‑end. The core responsibilities of
the backend include:

* Managing media in an S3 bucket (uploading images and listing gallery items).
* Creating payment intents via a third‑party payment provider (e.g. Stripe).
* Sending client notifications through AWS SNS.
* Fetching calendar events from a Notion database via the Notion REST API.

Environment variables drive all configuration so that sensitive credentials
are never committed into version control. See the README for details on
setting these variables before running the server.
"""

import os
from typing import List, Dict, Any

from flask import Flask, request, jsonify

try:
    import boto3  # AWS SDK for Python
except ImportError:
    boto3 = None  # type: ignore

try:
    import stripe  # Optional payment integration
except ImportError:
    stripe = None  # type: ignore

import requests  # For Notion API calls


def create_app() -> Flask:
    """Factory to create and configure the Flask application."""
    app = Flask(__name__)

    # Basic configuration via environment variables
    s3_bucket = os.environ.get("S3_BUCKET_NAME")
    notion_token = os.environ.get("NOTION_TOKEN")
    notion_database_id = os.environ.get("NOTION_DATABASE_ID")
    aws_region = os.environ.get("AWS_REGION", "us-east-1")
    stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY")

    # Initialize AWS clients lazily
    s3_client = None
    sns_client = None
    if boto3 is not None:
        if s3_bucket:
            s3_client = boto3.client("s3", region_name=aws_region)
        # Create SNS client for notifications (optional)
        sns_client = boto3.client("sns", region_name=aws_region)

    # Initialize Stripe if available
    if stripe is not None and stripe_secret_key:
        stripe.api_key = stripe_secret_key

    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check() -> Any:
        """Simple endpoint to verify that the service is running."""
        return jsonify({"status": "ok"})

    # Gallery endpoints
    @app.route("/api/gallery", methods=["GET", "POST"])
    def gallery() -> Any:
        """
        GET: Return a list of objects (images) in the configured S3 bucket.
        POST: Upload a new image to the bucket. Expects a multipart/form-data
        request with a file under the key "image".
        """
        if not s3_client or not s3_bucket:
            return jsonify({"error": "S3 is not configured"}), 500

        if request.method == "GET":
            # List objects in the bucket
            objects: List[Dict[str, Any]] = []
            try:
                resp = s3_client.list_objects_v2(Bucket=s3_bucket)
                for obj in resp.get("Contents", []):
                    key = obj.get("Key")
                    # Generate a presigned URL for each object so the client can download it
                    url = s3_client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": s3_bucket, "Key": key},
                        ExpiresIn=3600,
                    )
                    objects.append({"key": key, "url": url})
                return jsonify(objects)
            except Exception as exc:
                return jsonify({"error": str(exc)}), 500

        # Handle file upload
        file = request.files.get("image")
        if not file:
            return jsonify({"error": "No file provided"}), 400
        try:
            s3_client.upload_fileobj(file, s3_bucket, file.filename)
            return jsonify({"message": "File uploaded", "filename": file.filename})
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    # Payments endpoint
    @app.route("/api/payments", methods=["POST"])
    def create_payment() -> Any:
        """
        Create a payment intent for a session. This uses Stripe by default.
        The client should send JSON with `amount` (in cents), `currency` and
        optional metadata. Returns the client secret for the PaymentIntent.
        """
        if stripe is None or stripe_secret_key is None:
            return jsonify({"error": "Payments are not configured"}), 500

        data = request.get_json(force=True)
        amount = data.get("amount")
        currency = data.get("currency", "usd")
        if not amount:
            return jsonify({"error": "Amount is required"}), 400
        try:
            # Create a PaymentIntent with Stripe
            intent = stripe.PaymentIntent.create(
                amount=int(amount),
                currency=currency,
                metadata=data.get("metadata", {}),
            )
            return jsonify({"client_secret": intent.client_secret})
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    # Notifications endpoint
    @app.route("/api/notifications", methods=["POST"])
    def send_notification() -> Any:
        """
        Send a notification to a client using AWS SNS. Expects JSON with
        `subject`, `message`, and optionally `topic_arn` or `phone_number`.
        """
        if sns_client is None:
            return jsonify({"error": "SNS is not configured"}), 500

        data = request.get_json(force=True)
        subject = data.get("subject", "Notification")
        message = data.get("message")
        topic_arn = data.get("topic_arn")
        phone_number = data.get("phone_number")
        if not message:
            return jsonify({"error": "Message is required"}), 400

        try:
            if topic_arn:
                response = sns_client.publish(
                    TopicArn=topic_arn,
                    Message=message,
                    Subject=subject,
                )
            elif phone_number:
                response = sns_client.publish(
                    PhoneNumber=phone_number,
                    Message=message,
                )
            else:
                return jsonify({"error": "topic_arn or phone_number must be provided"}), 400
            return jsonify({"message_id": response.get("MessageId")})
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    # Calendar endpoint
    @app.route("/api/calendar", methods=["GET"])
    def get_calendar_events() -> Any:
        """
        Fetch upcoming events from a Notion database. Requires NOTION_TOKEN
        and NOTION_DATABASE_ID environment variables. Returns a list of events.
        """
        if not notion_token or not notion_database_id:
            return jsonify({"error": "Notion is not configured"}), 500

        notion_api_url = f"https://api.notion.com/v1/databases/{notion_database_id}/query"
        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(notion_api_url, headers=headers, json={})
            if resp.status_code != 200:
                return jsonify({"error": "Notion API returned an error", "details": resp.text}), 500
            data: Dict[str, Any] = resp.json()
            events: List[Dict[str, Any]] = []
            for page in data.get("results", []):
                # Basic parsing: extract date and title from properties
                properties = page.get("properties", {})
                title_props = properties.get("Name", {})
                title_items = title_props.get("title", [])
                title = "".join(item.get("plain_text", "") for item in title_items)
                date_props = properties.get("Date", {}).get("date", {})
                start = date_props.get("start")
                end = date_props.get("end")
                events.append({"title": title, "start": start, "end": end})
            return jsonify(events)
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    return app


if __name__ == "__main__":
    # When run directly, create the app and serve it
    application = create_app()
    application.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
