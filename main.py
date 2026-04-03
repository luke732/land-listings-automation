"""
Land Listing Automation — Webhook Server
=========================================
TWO-PHASE WORKFLOW:

PHASE 1 — "Write Ad" (Podio 'write-ad' field → Done):
  Fetches all property data → generates AI headlines + 1000-word description
  → writes back to Podio 'headlines' and 'special-ad-text' fields for Luke to review.

PHASE 2 — "Post Ad" (Podio 'post-ad' field → Done):
  Reads finalized ad content from Podio → builds full ad from template
  → posts to Carrot.com, Land.com, and LandFlip.com
  → stamps posting results back as a Podio comment.

Both phases are triggered by Podio Workflow Automation calling this webhook.
Set up TWO workflow automations in Podio — one for each trigger field.
"""
import logging
import os
import threading

from flask import Flask, request, jsonify

from config import PODIO_HOOK_ID, PORT, LOG_LEVEL
from podio_client import PodioClient
from ad_writer import generate_ad_copy
from ad_builder import build_ad
from carrot_poster import CarrotPoster
from browser_poster import LandComPoster, LandFlipPoster, run_async

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s  %(levelname)-8s  %(name)s  %(message)s',
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# ── Health check ──────────────────────────────────────────────────────────────

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'country-land-listing-automation'})


# ── Podio webhook ─────────────────────────────────────────────────────────────

@app.route('/webhook/podio', methods=['POST'])
def podio_webhook():
    data      = request.form.to_dict() if request.form else (request.json or {})
    hook_type = data.get('type', '')
    item_id   = data.get('item_id')

    logger.info(f"Podio webhook  type={hook_type}  item_id={item_id}")

    # One-time verification when you register the hook
    if hook_type == 'hook.verify':
        code    = data.get('code', '')
        hook_id = data.get('hook_id') or PODIO_HOOK_ID
        if code and hook_id:
            try:
                PodioClient().validate_webhook(int(hook_id), code)
            except Exception as exc:
                logger.error(f"Webhook verification failed: {exc}")
        return jsonify({'status': 'verified'})

    if hook_type in ('item.create', 'item.update') and item_id:
        # Determine which phase triggered this call via a query param
        # Set up TWO Podio Workflow Automations:
        #   Automation 1: when 'write-ad' changes → POST /webhook/podio?phase=write
        #   Automation 2: when 'post-ad' changes  → POST /webhook/podio?phase=post
        phase = request.args.get('phase', 'post')  # default to post for backwards compat

        if phase == 'write':
            t = threading.Thread(target=phase1_write_ad, args=(int(item_id),), daemon=True)
        else:
            t = threading.Thread(target=phase2_post_ad, args=(int(item_id),), daemon=True)

        t.start()
        return jsonify({'status': 'processing', 'phase': phase, 'item_id': item_id})

    return jsonify({'status': 'ignored'})


# ── Manual triggers (testing) ─────────────────────────────────────────────────

@app.route('/write/<int:item_id>', methods=['POST'])
def manual_write(item_id: int):
    """POST /write/12345 — trigger Phase 1 (ad writing) for a specific item."""
    threading.Thread(target=phase1_write_ad, args=(item_id,), daemon=True).start()
    return jsonify({'status': 'phase1_started', 'item_id': item_id})


@app.route('/post/<int:item_id>', methods=['POST'])
def manual_post(item_id: int):
    """POST /post/12345 — trigger Phase 2 (posting) for a specific item."""
    threading.Thread(target=phase2_post_ad, args=(item_id,), daemon=True).start()
    return jsonify({'status': 'phase2_started', 'item_id': item_id})


# ── Phase 1: Write Ad ─────────────────────────────────────────────────────────

def phase1_write_ad(item_id: int):
    """
    Generate AI ad copy and write it back to Podio for Luke to review.
    Triggered when the 'Write ad' field is marked Done.
    """
    logger.info(f"▶ PHASE 1: Writing ad for item {item_id}")
    podio = PodioClient()

    try:
        item = podio.get_item(item_id)
        prop = podio.extract_property_data(item)
        logger.info(f"  Property: {prop['acreage']} acres in {prop['county']}, {prop['state']}")
    except Exception as exc:
        logger.error(f"  Could not fetch item {item_id}: {exc}")
        return

    try:
        headlines, description = generate_ad_copy(prop)
        logger.info("  Ad copy generated")
    except Exception as exc:
        logger.error(f"  Ad generation failed: {exc}")
        podio.add_comment(item_id, f"❌ Ad writing failed: {exc}")
        return

    # Write back to Podio
    try:
        podio.update_text_field(item_id, 'headlines',    headlines)
        podio.update_text_field(item_id, 'special-ad-text', description)
        podio.add_comment(item_id,
            "✅ Ad copy generated and saved to 'Headlines' and 'Special Ad Text' fields.\n"
            "Please review, make any edits, then mark 'Post Ad' → Done to publish to all platforms."
        )
        logger.info(f"✅ Phase 1 complete for item {item_id}")
    except Exception as exc:
        logger.error(f"  Failed to write ad back to Podio: {exc}")
        podio.add_comment(item_id, f"❌ Could not save ad copy to Podio: {exc}")


# ── Phase 2: Post Ad ──────────────────────────────────────────────────────────

def phase2_post_ad(item_id: int):
    """
    Build the full ad and post to Carrot.com, Land.com, and LandFlip.com.
    Triggered when the 'Post Ad' field is marked Done.
    """
    logger.info(f"▶ PHASE 2: Posting ad for item {item_id}")
    podio   = PodioClient()
    results = {}

    try:
        item = podio.get_item(item_id)
        prop = podio.extract_property_data(item)
        logger.info(f"  Property: {prop['acreage']} acres in {prop['county']}, {prop['state']}")
    except Exception as exc:
        logger.error(f"  Could not fetch item {item_id}: {exc}")
        return

    # Use the finalized ad content from Podio
    headlines   = prop.get('headline', '')
    description = prop.get('description', '')

    if not description:
        podio.add_comment(item_id,
            "⚠️ No ad description found in 'Special Ad Text'. "
            "Please run Phase 1 (mark 'Write Ad' → Done) first, review the copy, then re-trigger posting."
        )
        return

    # Build the full ad document
    full_ad = build_ad(prop, headlines, description)

    # Download photos
    try:
        image_paths = podio.download_item_images(item_id, prop)
        logger.info(f"  {len(image_paths)} photos downloaded")
    except Exception as exc:
        logger.warning(f"  Photo download failed: {exc}")
        image_paths = []

    # ── Post to Carrot.com ────────────────────────────────────────────────
    try:
        carrot_url = CarrotPoster().create_listing(prop, full_ad, image_paths)
        results['Carrot.com'] = ('✅', carrot_url)
    except Exception as exc:
        logger.error(f"  Carrot posting failed: {exc}")
        results['Carrot.com'] = ('❌', str(exc))

    # ── Post to Land.com ──────────────────────────────────────────────────
    try:
        land_url = run_async(LandComPoster().post_listing(prop, full_ad, image_paths))
        results['Land.com'] = ('✅', land_url)
    except Exception as exc:
        logger.error(f"  Land.com failed: {exc}")
        results['Land.com'] = ('❌', str(exc))

    # ── Post to LandFlip.com ──────────────────────────────────────────────
    try:
        flip_url = run_async(LandFlipPoster().post_listing(prop, full_ad, image_paths))
        results['LandFlip.com'] = ('✅', flip_url)
    except Exception as exc:
        logger.error(f"  LandFlip failed: {exc}")
        results['LandFlip.com'] = ('❌', str(exc))

    # ── Report back to Podio ──────────────────────────────────────────────
    lines = [f"Listing posted: {prop['acreage']} acres in {prop['county']}, {prop['state']}\n"]
    for platform, (status, detail) in results.items():
        lines.append(f"{status} {platform}: {detail}")

    podio.add_comment(item_id, '\n'.join(lines))

    # Stamp the "Ad posted on Land Search" field
    try:
        podio.update_text_field(item_id, 'ad-posted-on-mls-2', 'Yes')
    except Exception:
        pass

    all_ok = all(s == '✅' for s, _ in results.values())
    logger.info(f"{'✅' if all_ok else '⚠️'}  Phase 2 complete for item {item_id}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    logger.info(f"Starting Country Land Group listing automation on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
