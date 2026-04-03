"""
Land Listing Automation - Configuration
All settings loaded from environment variables (.env file or Railway Variables tab).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Podio API ──────────────────────────────────────────────────────────────────
PODIO_CLIENT_ID     = os.environ.get('PODIO_CLIENT_ID',     'listing-automation')
PODIO_CLIENT_SECRET = os.environ.get('PODIO_CLIENT_SECRET', 'zx7h9tCAZnGHtJPdq7QCZy7Pfb878jmnAWQGY9Cl4uKTbjGgecik1XXbiPtpfBHd')
PODIO_APP_ID        = os.environ.get('PODIO_APP_ID',        '20192346')
PODIO_APP_TOKEN     = os.environ.get('PODIO_APP_TOKEN',     '223497506afc487eace914852f2b169d')
PODIO_HOOK_ID       = os.environ.get('PODIO_HOOK_ID',       '')

# ── Podio Field External IDs ───────────────────────────────────────────────────
# Core listing fields
PODIO_FIELD_UNIQUE_ID       = 'unique-id'
PODIO_FIELD_ADDRESS         = 'property-address-no-street'
PODIO_FIELD_ACREAGE         = 'property-size-acres'
PODIO_FIELD_COORDINATES     = 'coordinates-2'
PODIO_FIELD_COUNTY          = 'county-2'           # app-relation type
PODIO_FIELD_STATE           = 'state-2'            # app-relation type
PODIO_FIELD_ZONING          = 'zoning-2'           # app-relation type
PODIO_FIELD_PARCEL          = 'apnparcel'
PODIO_FIELD_LEGAL_DESC      = 'legal-description-2'
PODIO_FIELD_ELEVATION       = 'elevation-2'
PODIO_FIELD_TAX_ACCOUNT     = 'tax-account-2'
PODIO_FIELD_YEARLY_TAXES    = 'yearly-tax-amount'
PODIO_FIELD_GOOGLE_MAPS     = 'google-map-directions'
PODIO_FIELD_LANDID_LINK     = 'landid-link'
PODIO_FIELD_HOA             = 'is-this-part-of-an-hoa'
PODIO_FIELD_UTILITIES       = 'electric-water-source-well-or-city-and-sewer-septic-or-'
PODIO_FIELD_ROAD_ACCESS     = 'road-frontage'      # category type
PODIO_FIELD_MAPRIGHT        = 'mapright-map-code'
PODIO_FIELD_NOTES           = 'note'
PODIO_FIELD_NOTES_ON_SURVEY = 'notes-on-survey'

# Pricing fields
PODIO_FIELD_CASH_PRICE      = 'cash-discount-price-2'
PODIO_FIELD_FINANCED_PRICE  = 'owner-financed-price-only-fill-if-different-than-cash-p'
PODIO_FIELD_DOWN_PAYMENT    = 'down-payment-5'
PODIO_FIELD_MONTHLY_PAYMENT = 'monthly-payments-2'
PODIO_FIELD_LOAN_TERM       = 'loan-term'

# Ad content fields
PODIO_FIELD_HEADLINE        = 'headlines'
PODIO_FIELD_DESCRIPTION     = 'special-ad-text'    # AI-generated 1000-word ad goes here
PODIO_FIELD_DRONE_NOTES     = 'notes-on-drone-status'

# Image fields
PODIO_FIELD_COVER_PHOTO     = 'cover-photo'
PODIO_FIELD_PROPERTY_IMAGES = 'property-images'

# Workflow trigger fields
PODIO_FIELD_WRITE_AD        = 'write-ad'           # Phase 1: write ad copy
PODIO_FIELD_POST_AD         = 'post-ad'            # Phase 2: post to listing sites
PODIO_FIELD_AD_POSTED_LAND  = 'ad-posted-on-mls-2' # stamp after posting

# ── AI / Claude API ────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

# ── Carrot.com (WordPress REST API) ───────────────────────────────────────────
CARROT_SITE_URL      = os.environ.get('CARROT_SITE_URL',      '').rstrip('/')
CARROT_USERNAME      = os.environ.get('CARROT_USERNAME',      '')
CARROT_APP_PASSWORD  = os.environ.get('CARROT_APP_PASSWORD',  '')
CARROT_POST_CATEGORY = os.environ.get('CARROT_POST_CATEGORY', 'land-for-sale')

# ── Land.com ──────────────────────────────────────────────────────────────────
LAND_COM_USERNAME = os.environ.get('LAND_COM_USERNAME', '')
LAND_COM_PASSWORD = os.environ.get('LAND_COM_PASSWORD', '')

# ── LandFlip.com ──────────────────────────────────────────────────────────────
LANDFLIP_USERNAME = os.environ.get('LANDFLIP_USERNAME', '')
LANDFLIP_PASSWORD = os.environ.get('LANDFLIP_PASSWORD', '')

# ── General ───────────────────────────────────────────────────────────────────
DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', '/tmp/property_images')
LOG_LEVEL    = os.environ.get('LOG_LEVEL',    'INFO')
PORT         = int(os.environ.get('PORT',     5000))
