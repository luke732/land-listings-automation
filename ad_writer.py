"""
Ad Writer — Phase 1
Uses Claude AI to generate compelling property ad copy based on the
Country Land Group 41-point ad writing checklist.

The output (headlines + 1000-word description) is written back to
the Podio 'headlines' and 'special-ad-text' fields for Luke to review
before posting goes out.
"""
import logging
import anthropic
from config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)


def generate_ad_copy(prop: dict) -> tuple:
    """
    Generate headlines and a ~1000-word listing description.
    Returns (headlines: str, description: str)
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Build the checklist bullet points from available Podio data
    bullets = _build_checklist_bullets(prop)
    bullet_text = '\n'.join(f'• {b}' for b in bullets if b)

    acreage  = prop.get('acreage', '')
    county   = prop.get('county', '')
    state    = prop.get('state', '')
    cash_price = prop.get('cash_price')
    price_str  = f'${cash_price:,.0f}' if cash_price else 'Contact for price'
    is_financed = prop.get('is_owner_financed', False)

    financing_note = ''
    if is_financed:
        dp  = prop.get('down_payment')
        mo  = prop.get('monthly_payment')
        trm = prop.get('loan_term')
        if dp and mo:
            financing_note = f'Owner financing available: ${dp:,.0f} down, ${mo:,.0f}/month for {int(trm or 0)} months.'

    prompt = f"""You are writing a real estate listing ad for Country Land Group, a land investment company.

Property overview:
- {acreage} acres in {county} County, {state}
- Cash price: {price_str}
{('- ' + financing_note) if financing_note else ''}

Property details gathered from our research:
{bullet_text}

Please write the following TWO things:

1. HEADLINES (3-5 punchy bullet points highlighting the best features — examples: "Unrestricted Land!", "Owner Financing Available!", "Creek on the Property!", "Below Appraised Value!", "Perk Test Passed!"). Keep each headline short and exciting. Return these as a plain bulleted list.

2. LISTING DESCRIPTION (approximately 1000 words). Write an engaging, honest property listing that:
- Opens with an exciting lead paragraph about the property's best features
- Covers all the key details from the research bullets above
- Uses a warm, professional tone appropriate for land buyers (hunters, homesteaders, investors, families)
- Mentions owner financing terms prominently if available
- Ends with: "Buyer to verify all of the above."
- Does NOT include the property address, price, parcel number, or legal description (those go in a separate section)

Separate the HEADLINES and DESCRIPTION with the marker: ---DESCRIPTION---
"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    full_response = message.content[0].text

    # Split into headlines and description
    if '---DESCRIPTION---' in full_response:
        parts = full_response.split('---DESCRIPTION---', 1)
        headlines   = parts[0].strip()
        description = parts[1].strip()
    else:
        # Fallback: treat first paragraph as headline, rest as description
        lines = full_response.strip().split('\n')
        headlines   = lines[0]
        description = '\n'.join(lines[1:]).strip()

    logger.info(f"Generated ad copy ({len(description.split())} words)")
    return headlines, description


def _build_checklist_bullets(prop: dict) -> list:
    """
    Convert Podio property data into the 41-point checklist bullet format
    used in the Country Land Group ad writing process.
    """
    bullets = []

    def add(label, value):
        if value:
            bullets.append(f"{label}: {value}")

    # Location & size
    add("Acreage", prop.get('acreage'))
    add("County", prop.get('county'))
    add("State", prop.get('state'))
    add("Coordinates", prop.get('coordinates'))
    add("Elevation", prop.get('elevation'))

    # Access & roads
    add("Road frontage", prop.get('road_access'))
    add("Google Maps link", prop.get('google_maps_link'))

    # Utilities
    utilities = prop.get('utilities', '')
    if utilities:
        bullets.append(f"Utilities/water/sewer/electric: {utilities}")

    # Zoning & use
    add("Zoning", prop.get('zoning'))
    add("HOA or road maintenance fees", prop.get('hoa'))

    # Legal & survey
    add("Survey status", prop.get('notes_on_survey'))
    add("Legal description", prop.get('legal_desc'))
    add("APN/Parcel number", prop.get('parcel_apn'))

    # Financial
    cash = prop.get('cash_price')
    if cash:
        bullets.append(f"Cash discount price: ${cash:,.0f}")
    if prop.get('is_owner_financed'):
        fp  = prop.get('financed_price')
        dp  = prop.get('down_payment')
        mo  = prop.get('monthly_payment')
        trm = prop.get('loan_term')
        if fp:
            bullets.append(f"Owner financed price: ${fp:,.0f}")
        if dp and mo:
            bullets.append(f"Owner financing terms: ${dp:,.0f} down, ${mo:,.0f}/month for {int(trm or 0)} months")
    add("Yearly taxes", prop.get('yearly_taxes'))

    # Drone & site visit notes
    drone = prop.get('drone_notes', '')
    if drone:
        bullets.append(f"Drone/site visit notes: {drone}")

    # General notes from Podio
    notes = prop.get('notes', '')
    if notes:
        bullets.append(f"Additional notes: {notes}")

    # LandID link for map reference
    add("LandID map link", prop.get('landid_link'))

    return bullets
