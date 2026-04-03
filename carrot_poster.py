"""
Carrot.com Poster
Posts the full built ad to your Carrot website via the WordPress REST API.
"""
import base64
import logging
import requests
from pathlib import Path
from config import CARROT_SITE_URL, CARROT_USERNAME, CARROT_APP_PASSWORD, CARROT_POST_CATEGORY

logger = logging.getLogger(__name__)


class CarrotPoster:
    def __init__(self):
        creds      = f"{CARROT_USERNAME}:{CARROT_APP_PASSWORD}"
        self._auth = base64.b64encode(creds.encode()).decode()

    def _headers(self, content_type='application/json'):
        h = {'Authorization': f'Basic {self._auth}'}
        if content_type:
            h['Content-Type'] = content_type
        return h

    def _api(self, path):
        return f"{CARROT_SITE_URL}/wp-json/wp/v2/{path}"

    def upload_image(self, image_path: str) -> tuple:
        p    = Path(image_path)
        ext  = p.suffix.lower()
        mime = 'image/jpeg' if ext in ('.jpg', '.jpeg') else 'image/png'
        headers = {
            'Authorization':       f'Basic {self._auth}',
            'Content-Disposition': f'attachment; filename="{p.name}"',
            'Content-Type':        mime,
        }
        with open(image_path, 'rb') as fh:
            resp = requests.post(self._api('media'), headers=headers, data=fh.read())
        resp.raise_for_status()
        media = resp.json()
        logger.info(f"Uploaded image → media ID {media['id']}")
        return media['id'], media.get('source_url', '')

    def _get_or_create_category(self, name: str) -> int:
        resp = requests.get(self._api('categories'), params={'search': name}, headers=self._headers())
        cats = resp.json()
        if cats:
            return cats[0]['id']
        resp = requests.post(self._api('categories'), json={'name': name}, headers=self._headers())
        resp.raise_for_status()
        return resp.json()['id']

    def create_listing(self, property_data: dict, full_ad_text: str, image_paths: list = None) -> str:
        """
        Create a published listing post on Carrot using the fully built ad text.
        Returns the live URL.
        """
        prop = property_data

        # Upload images
        featured_id = None
        for i, img in enumerate(image_paths or [])[:10]:
            try:
                mid, _ = self.upload_image(img)
                if i == 0:
                    featured_id = mid
            except Exception as exc:
                logger.warning(f"Image upload skipped ({img}): {exc}")

        # Category
        cat_id = self._get_or_create_category(CARROT_POST_CATEGORY)

        # Title
        acreage = prop.get('acreage', '')
        county  = prop.get('county', '')
        state   = prop.get('state', '')
        title   = prop.get('title') or f"{acreage} Acres For Sale in {county} County, {state}"

        # Convert plain text ad to basic HTML for WordPress
        html_content = '<br>\n'.join(
            f'<p>{line}</p>' if line.strip() else ''
            for line in full_ad_text.split('\n')
        )

        post_data = {
            'title':      title,
            'content':    html_content,
            'status':     'publish',
            'categories': [cat_id],
        }
        if featured_id:
            post_data['featured_media'] = featured_id

        resp = requests.post(self._api('posts'), json=post_data, headers=self._headers())
        resp.raise_for_status()
        post = resp.json()
        url  = post.get('link', '')
        logger.info(f"Carrot listing live: {url}")
        return url
