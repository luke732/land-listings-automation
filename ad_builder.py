"""
Ad Builder — assembles the full Country Land Group ad using the two templates.

Template selection:
  - is_owner_financed = True  → Owner-Financing Ad template
  - is_owner_financed = False → Cash-only Ad template

The built ad is returned as a plain-text string suitable for:
  1. Posting as the listing body on Carrot, Land.com, LandFlip
  2. Saving as a .txt file for Google Drive
"""
import logging

logger = logging.getLogger(__name__)

# ── Static boilerplate (same in both templates) ───────────────────────────────

CONTACT_BLOCK = """Contact us Today.
Interested in this property? Call, text, or email us today for more details!
   (541) 375-0012
or
sales@countrylandsellers.com
Feel free to visit the property any time, no need to set up an appointment, this property has no address, the directions can be found in the google map link below.
Subscribe to email alerts by texting your e-mail address to (541) 375-0012 and be the first to know when we get a great deal in.
By texting (541) 375-0012 you authorize Country Land Group to send text messages with offers & other information, possibly using automated technology, to the number you provided. Message/data rates apply. Consent is not a condition of purchase. You may unsubscribe at any time."""

FOOTER_BLOCK = """If this property is not what you are looking for, go to our website at www.countrylandsellers.com and sign up for our deal alerts; you will be notified whenever we have a new property for sale! Or, e-mail, call or text us, and we may be able to find the property you are looking for.

Disclaimers: This property is being sold "as is". We do our best to collect accurate information, but we cannot guarantee that any of the information in this ad is correct, we recommend each buyer do their own research. We do our best to get pictures of the actual property, but they may not be of the property we are advertising. This Property is being sold "as is", the information we have listed in this ad may or may not be correct, but it is what we found when we researched this property. Please talk to a surveyor if you wish to verify the size of the property, the property may not be the size we have listed in the ad, we are just relaying the information the county has on the property. Under no circumstances do we ever do refunds on any property, it is the buyers responsibility to do their own due diligence before buying."""

OWNER_FIN_DISCLAIMER = "*Applicable fees may apply including but not limited to $35/month servicing fee and 12.9% interest for owner financing. Buyer is responsible for annual property tax. Contact Country Land Sellers for more details. Monthly payment subject to change based on down payment. Monthly payment shown is an estimate only."

DEPOSIT_NOTE = "*There is a $1000 deposit required with all purchases. $500 is a non refundable transaction fee and the remaining $500 would be applied to the purchase price at time of closing."


def build_ad(prop: dict, headlines: str, description: str) -> str:
    """
    Build the full ad text using the appropriate template.
    Returns a complete, ready-to-post string.
    """
    acreage = prop.get('acreage', '')
    county  = prop.get('county', '')
    state   = prop.get('state', '')
    is_of   = prop.get('is_owner_financed', False)

    # ── Header ────────────────────────────────────────────────────────────────
    header = f"{acreage} Acres\nFor Sale in\n{county} County {state}"

    # ── Headline block ────────────────────────────────────────────────────────
    headline_block = headlines.strip() if headlines else ''

    # ── Description block ─────────────────────────────────────────────────────
    description_block = description.strip() if description else ''

    # ── Links block ───────────────────────────────────────────────────────────
    maps_link   = prop.get('google_maps_link', '') or 'Link To Google Map Directions'
    county_gis  = '[County GIS Website Link]'
    landid_link = prop.get('landid_link', '') or '[Link to Map of Property]'

    links_block = f"Link To Google Map Directions: {maps_link}\nCounty GIS Website Link: {county_gis}\nLink to Map of Property: {landid_link}"

    # ── Price block ───────────────────────────────────────────────────────────
    cash_price = prop.get('cash_price')
    cash_str   = f"${cash_price:,.0f}" if cash_price else 'Contact for price'

    if is_of:
        fin_price = prop.get('financed_price') or cash_price
        fin_str   = f"${fin_price:,.0f}" if fin_price else 'Contact for price'
        dp        = prop.get('down_payment')
        mo        = prop.get('monthly_payment')
        trm       = prop.get('loan_term')
        dp_str    = f"${dp:,.0f}" if dp else '___'
        mo_str    = f"${mo:,.0f}" if mo else '___'
        trm_str   = str(int(trm)) if trm else '___'

        price_block = (
            f"Cash Discount Price: {cash_str}\n"
            f"{DEPOSIT_NOTE}\n"
            f"Owner Financed Price: {fin_str}\n"
            f"Owner Financing Terms: {dp_str} down and {mo_str}/month for {trm_str} months.\n"
            f"{OWNER_FIN_DISCLAIMER}"
        )
    else:
        price_block = (
            f"Cash Discount Price: {cash_str}    (Unfortunately we cannot offer owner financing on this property.)\n"
            f"{DEPOSIT_NOTE}"
        )

    # ── Details block ─────────────────────────────────────────────────────────
    def line(label, value, fallback=''):
        v = str(value).strip() if value else fallback
        return f"{label}: {v}"

    zoning = prop.get('zoning', '')
    hoa    = prop.get('hoa', '')
    survey = prop.get('notes_on_survey', '')

    details_block = '\n'.join([
        line("Address",                   prop.get('address')),
        line("County",                    county),
        line("Acres",                     f"{acreage} Acres (Raw Land)"),
        line("Coordinates",               prop.get('coordinates')),
        line("Parcel #",                  prop.get('parcel_apn')),
        line("Tax Account #",             prop.get('tax_account')),
        line("Yearly Estimated Taxes",    prop.get('yearly_taxes')),
        line("Elevation",                 prop.get('elevation')),
        line("Zoning",                    zoning if zoning else '[Zoning N/A — omit if not available]'),
        line("County Planning and zoning phone #", ''),
        line("Link to zoning info on county website", ''),
        line("Does this property have an HOA?",    hoa or 'No'),
        line("Does this property have a survey?",  survey or 'No'),
        line("Elementary school",         ''),
        line("Middle school",             ''),
        line("High school",               ''),
        line("Phone # for electric company", ''),
        line("Legal Description",         prop.get('legal_desc')),
    ])

    # ── Property ID ───────────────────────────────────────────────────────────
    property_id = prop.get('unique_id', '')

    # ── Assemble ──────────────────────────────────────────────────────────────
    sections = [
        header,
        '',
        headline_block,
        '',
        description_block,
        '',
        CONTACT_BLOCK,
        '',
        links_block,
        '',
        price_block,
        '',
        details_block,
        '',
        FOOTER_BLOCK,
        '',
        f"Property ID: {property_id}",
    ]

    full_ad = '\n'.join(sections)
    logger.info(f"Built {'owner-financed' if is_of else 'cash-only'} ad ({len(full_ad)} chars)")
    return full_ad
