"""
Podio API Client
Fetches all property fields, downloads images, writes back ad content, and manages webhooks.
"""
import os
import logging
import requests
import config as C

logger = logging.getLogger(__name__)
BASE_URL = "https://api.podio.com"


class PodioClient:
    def __init__(self):
        self.access_token = None
        self._authenticate()

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _authenticate(self):
        resp = requests.post(f"{BASE_URL}/oauth/token", data={
            'grant_type':    'app',
            'app_id':        C.PODIO_APP_ID,
            'app_token':     C.PODIO_APP_TOKEN,
            'client_id':     C.PODIO_CLIENT_ID,
            'client_secret': C.PODIO_CLIENT_SECRET,
        })
        resp.raise_for_status()
        self.access_token = resp.json()['access_token']
        logger.info("Authenticated with Podio API")

    def _headers(self):
        return {'Authorization': f'OAuth2 {self.access_token}'}

    # ── Item fetch ────────────────────────────────────────────────────────────

    def get_item(self, item_id: int) -> dict:
        resp = requests.get(f"{BASE_URL}/item/{item_id}", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def extract_property_data(self, item: dict) -> dict:
        """
        Extract every field needed for ad writing and posting.
        Handles text, number, category, app-relation, and image field types.
        """
        fields = {f['external_id']: f for f in item.get('fields', [])}

        def text(fid):
            f = fields.get(fid)
            if not f:
                return ''
            vals = f.get('values', [])
            return str(vals[0].get('value', '')).strip() if vals else ''

        def number(fid):
            f = fields.get(fid)
            if not f:
                return None
            vals = f.get('values', [])
            return vals[0].get('value') if vals else None

        def category(fid):
            """Returns list of selected option text strings."""
            f = fields.get(fid)
            if not f:
                return []
            return [v.get('value', {}).get('text', '') for v in f.get('values', [])]

        def app_relation(fid):
            """App-relation field (county-2, state-2, zoning-2) → title of linked item."""
            f = fields.get(fid)
            if not f:
                return ''
            vals = f.get('values', [])
            if not vals:
                return ''
            inner = vals[0].get('value', {})
            return (inner.get('title') or inner.get('name') or '').strip()

        def image_file_ids(fid):
            """Image field → list of (file_id, filename) tuples."""
            f = fields.get(fid)
            if not f:
                return []
            results = []
            for v in f.get('values', []):
                val = v.get('value', {})
                fid_val = val.get('file_id') or val.get('id')
                fname   = val.get('name', f'image_{fid_val}.jpg')
                if fid_val:
                    results.append((fid_val, fname))
            return results

        # Determine ad type: owner-financed if financed price OR monthly payment is set
        financed_price  = number(C.PODIO_FIELD_FINANCED_PRICE)
        monthly_payment = number(C.PODIO_FIELD_MONTHLY_PAYMENT)
        is_owner_financed = bool(financed_price or monthly_payment)

        cash_price = number(C.PODIO_FIELD_CASH_PRICE)

        return {
            # Identity
            'item_id':         item['item_id'],
            'title':           item.get('title', ''),
            'unique_id':       text(C.PODIO_FIELD_UNIQUE_ID),

            # Location
            'address':         text(C.PODIO_FIELD_ADDRESS),
            'county':          app_relation(C.PODIO_FIELD_COUNTY),
            'state':           app_relation(C.PODIO_FIELD_STATE),
            'coordinates':     text(C.PODIO_FIELD_COORDINATES),

            # Size & legal
            'acreage':         text(C.PODIO_FIELD_ACREAGE),
            'parcel_apn':      text(C.PODIO_FIELD_PARCEL),
            'legal_desc':      text(C.PODIO_FIELD_LEGAL_DESC),
            'elevation':       text(C.PODIO_FIELD_ELEVATION),
            'tax_account':     text(C.PODIO_FIELD_TAX_ACCOUNT),
            'yearly_taxes':    text(C.PODIO_FIELD_YEARLY_TAXES),

            # Zoning & use
            'zoning':          app_relation(C.PODIO_FIELD_ZONING),
            'road_access':     ', '.join(category(C.PODIO_FIELD_ROAD_ACCESS)),
            'hoa':             text(C.PODIO_FIELD_HOA),
            'utilities':       text(C.PODIO_FIELD_UTILITIES),
            'notes_on_survey': text(C.PODIO_FIELD_NOTES_ON_SURVEY),

            # Links
            'google_maps_link': text(C.PODIO_FIELD_GOOGLE_MAPS),
            'landid_link':      text(C.PODIO_FIELD_LANDID_LINK),
            'mapright_code':    text(C.PODIO_FIELD_MAPRIGHT),

            # Pricing
            'is_owner_financed': is_owner_financed,
            'cash_price':        cash_price,
            'financed_price':    financed_price,
            'down_payment':      number(C.PODIO_FIELD_DOWN_PAYMENT),
            'monthly_payment':   monthly_payment,
            'loan_term':         number(C.PODIO_FIELD_LOAN_TERM),

            # Ad content (may already be written)
            'headline':    text(C.PODIO_FIELD_HEADLINE),
            'description': text(C.PODIO_FIELD_DESCRIPTION),
            'drone_notes': text(C.PODIO_FIELD_DRONE_NOTES),
            'notes':       text(C.PODIO_FIELD_NOTES),

            # Images
            '_cover_photo_ids':     image_file_ids(C.PODIO_FIELD_COVER_PHOTO),
            '_property_image_ids':  image_file_ids(C.PODIO_FIELD_PROPERTY_IMAGES),
        }

    # ── Image download ────────────────────────────────────────────────────────

    def download_file(self, file_id: int, filename: str, download_dir: str) -> str:
        resp = requests.get(
            f"{BASE_URL}/file/{file_id}/raw",
            headers=self._headers(),
            stream=True,
        )
        resp.raise_for_status()
        os.makedirs(download_dir, exist_ok=True)
        filepath = os.path.join(download_dir, filename)
        with open(filepath, 'wb') as fh:
            for chunk in resp.iter_content(8192):
                fh.write(chunk)
        logger.info(f"Downloaded: {filepath}")
        return filepath

    def download_item_images(self, item_id: int, prop: dict) -> list:
        """Download cover photo first, then property images. Returns local paths."""
        download_dir = os.path.join(C.DOWNLOAD_DIR, str(item_id))
        paths = []
        all_refs = prop.get('_cover_photo_ids', []) + prop.get('_property_image_ids', [])
        for fid, fname in all_refs[:20]:
            try:
                path = self.download_file(fid, fname, download_dir)
                paths.append(path)
            except Exception as exc:
                logger.warning(f"Skipping image {fname}: {exc}")
        logger.info(f"Downloaded {len(paths)} images for item {item_id}")
        return paths

    # ── Write back to Podio ───────────────────────────────────────────────────

    def update_text_field(self, item_id: int, external_id: str, value: str):
        """Write a text value back to a Podio field."""
        resp = requests.put(
            f"{BASE_URL}/item/{item_id}/value/{external_id}",
            json=[{'value': value}],
            headers=self._headers(),
        )
        resp.raise_for_status()
        logger.info(f"Updated '{external_id}' on item {item_id}")

    def add_comment(self, item_id: int, text: str):
        resp = requests.post(
            f"{BASE_URL}/comment/item/{item_id}",
            json={'value': text},
            headers=self._headers(),
        )
        resp.raise_for_status()
        logger.info(f"Added comment to item {item_id}")

    # ── Webhook helpers ───────────────────────────────────────────────────────

    def register_webhook(self, app_id: int, url: str) -> int:
        resp = requests.post(
            f"{BASE_URL}/hook/app/{app_id}/",
            json={'url': url, 'type': 'item.update'},
            headers=self._headers(),
        )
        resp.raise_for_status()
        hook_id = resp.json()['hook_id']
        logger.info(f"Registered webhook {hook_id} → {url}")
        return hook_id

    def validate_webhook(self, hook_id: int, code: str):
        resp = requests.post(
            f"{BASE_URL}/hook/{hook_id}/verify/validate",
            json={'code': code},
            headers=self._headers(),
        )
        resp.raise_for_status()
        logger.info(f"Validated webhook {hook_id}")
