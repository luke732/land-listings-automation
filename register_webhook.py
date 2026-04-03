"""
One-time script: Register the Podio webhook after you deploy.

Usage:
  python register_webhook.py https://your-app.railway.app/webhook/podio

This prints the hook_id — copy it into your .env as PODIO_HOOK_ID.
"""
import sys
from podio_client import PodioClient
from config import PODIO_APP_ID

def main():
    if len(sys.argv) < 2:
        print("Usage: python register_webhook.py <your_webhook_url>")
        print("Example: python register_webhook.py https://myapp.railway.app/webhook/podio")
        sys.exit(1)

    webhook_url = sys.argv[1]
    podio = PodioClient()
    hook_id = podio.register_webhook(int(PODIO_APP_ID), webhook_url)
    print(f"\n✅ Webhook registered!")
    print(f"   hook_id = {hook_id}")
    print(f"\n👉 Add this to your .env file:")
    print(f"   PODIO_HOOK_ID={hook_id}")
    print(f"\nPodio will send a verification request to your endpoint shortly.")
    print("The server handles this automatically if PODIO_HOOK_ID is set.")

if __name__ == '__main__':
    main()
