import uuid

import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_API_KEY
pk_key = settings.STRIPE_PUBLISHABLE_KEY


class StripeAPI:
    
    @classmethod
    def create_customer(cls, name, email, phone, **kwargs):
        customer = stripe.Customer.create(
            name=name,
            phone=phone,
            email=email,
        )
        return customer
    
    @classmethod
    def retrieve_customer(cls, customer_id):
        from edudream.modules.utils import log_request
        customer = stripe.Customer.retrieve(customer_id)
        log_request(f'Stripe customer: {customer}')
        return customer

    @classmethod
    def calculate_tax(cls, customer_id, amount, ip_address):
        from edudream.modules.utils import log_request
        result = stripe.tax.Calculation.create(
                  currency="eur",
                  line_items=[
                      {
                          "amount": int(amount) * 100,
                          "reference": f"Tax calculation for customer: {customer_id} - {uuid.uuid4()}"
                      }
                  ],
                  customer_details={"ip_address": ip_address}
                )
        log_request(f'Stripe setup response: {result}')
        return result

    @classmethod
    def create_payment_session(cls, name, amount, **kwargs):
        from edudream.modules.utils import log_request
        from edudream.modules.utils import get_site_details
        site_setting = get_site_details()
        frontend_base_url = site_setting.frontend_url

        """
        Initiate a stripe transaction
        """
        try:
            return_url = kwargs.get('return_url', )
            customer_id = kwargs.get('customer_id', )
            stripe_payment = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "eur",
                            "product_data": {
                                "name": name,
                            },
                            "unit_amount": int(amount) * 100,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=return_url + '&reference={CHECKOUT_SESSION_ID}',
                cancel_url=f"{frontend_base_url}/verify-checkout?status={str(False).lower()}",
                customer=customer_id,
            )
            return True, stripe_payment
        except Exception as err:
            # traceback.print_exc()
            log_request(f"Error generating payment Link: {err}")
            return False, f"{err}"

    @classmethod
    def attach_payment_method(cls, payment_method_id, customer_id):
        from edudream.modules.utils import log_request
        result = stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
        log_request(f'Stripe payment method attached: {result}')
        return result

    @classmethod
    def retrieve_checkout_session(cls, session_id):
        from edudream.modules.utils import log_request
        result = stripe.checkout.Session.retrieve(session_id)
        log_request(f'Stripe retrieve checkout session: {result}')
        return result
    
    @classmethod
    def retrieve_setup_intent(cls, setup_intent):
        from edudream.modules.utils import log_request
        result = stripe.SetupIntent.retrieve(setup_intent)
        log_request(f'Stripe setup response: {result}')
        return result
    
    @classmethod
    def retrieve_payment_method(cls, payment_method_id):
        from edudream.modules.utils import log_request
        result = stripe.PaymentMethod.retrieve(payment_method_id)
        log_request(f'Stripe setup response: {result}')
        return result

    @classmethod
    def auto_charge_with_payment_method(cls, amount, currency_code, payment_method_id, **kwargs):
        from edudream.modules.utils import log_request
        description = kwargs.get('description', )
        customer_id = kwargs.get('customer_id', )
        # metadata = kwargs.get('metadata', {})
        # if type(metadata) is not dict:
        #     return False, create_error_message('metadata', "metadata must be a dictionary")
        
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                payment_method=payment_method_id,
                currency=currency_code,
                confirm=True,
                # return_url=return_url,
                description=description,
                # metadata=metadata,
                payment_method_types=[
                    'card',
                ],
                setup_future_usage='off_session',
                customer=customer_id,
            )
            log_request(intent)
            return True, intent
        except Exception as ex:
            log_request(f"Error occurred on Create PaymentIntent: {ex}")
            return False, str(ex)
    
    @classmethod
    def retrieve_payment_intent(cls, payment_intent):
        return stripe.PaymentIntent.retrieve(payment_intent)

    @classmethod
    def upload_file(cls, file_path, purpose):
        from edudream.modules.utils import log_request
        with open(file_path, "rb") as fp:
            upload = stripe.File.create(purpose=purpose, file=fp)
            log_request(f'File upload response: {upload}')
            return upload

    @classmethod
    def create_connect_account(cls, user):
        from edudream.modules.utils import log_request
        # city_name = str(user.profile.city)
        # country_code = str(user.profile.country.alpha2code)
        # state_name = str(user.profile.state.name)
        # postal_code = str(user.profile.postal_code)
        # address = str(user.profile.address)
        account_token = stripe.Token.create(
            account={"individual": {"first_name": str(user.first_name), "last_name": str(user.last_name),
                                    "email": str(user.email)}, "tos_shown_and_accepted": True,
                     "business_type": "individual"}, api_key=pk_key
        )
        log_request(f'Account creation token response: {account_token}')

        result = stripe.Account.create(
            type="custom", country="FR", email=str(user.email),
            capabilities={"card_payments": {"requested": True}, "transfers": {"requested": True}, },
            account_token=account_token.get("id"),
            # individual={
            #     "first_name": str(user.first_name), "last_name": str(user.last_name), "email": str(user.email),
            #     "address": {"city": city_name, "country": country_code, "line1": address,
            #                 "postal_code": postal_code, "state": state_name},
            # }
        )
        log_request(f'Connect account creation response: {result}')
        return result

    @classmethod
    def update_connect_account(cls, user, address_front_file, address_back_file, nat_front_file, nat_back_file):
        from edudream.modules.utils import log_request
        account_token = stripe.Token.create(
            account={"individual": {"first_name": str(user.first_name), "last_name": str(user.last_name),
                                    "email": str(user.email)}, "tos_shown_and_accepted": True,
                     "business_type": "individual"}, api_key=pk_key
        )
        log_request(f'Account creation token response: {account_token}')

        result = stripe.Account.modify(
            str(user.profile.stripe_connect_account_id), account_token=account_token.get("id"), individual={
                "verification": {"document": {"front": str(nat_front_file), "back": str(nat_back_file)},
                                 "additional_document": {"front": str(address_front_file),
                                                         "back": str(address_back_file)}}}
        )
        log_request(f'Connect account update response: {result}')
        return result

    @classmethod
    def create_account_link(cls, acct):
        from edudream.modules.utils import log_request, get_site_details
        site_setting = get_site_details()
        frontend_base_url = site_setting.frontend_url

        result = stripe.AccountLink.create(
            account=acct,
            refresh_url=f"{frontend_base_url}/complete-onboarding?status={str(False).lower()}",
            return_url=f"{frontend_base_url}/complete-onboarding?status={str(True).lower()}",
            type="account_onboarding",
        )
        log_request(f'Account link response: {result}')
        return result

    @classmethod
    def create_connect_account_token(cls, user):
        from edudream.modules.utils import log_request
        result = stripe.Token.create(
            account={"individual": {"first_name": str(user.first_name), "last_name": str(user.last_name),
                                    "email": str(user.email)}, "tos_shown_and_accepted": True, },
        )
        log_request(f'Account creation token response: {result}')
        return result

    @classmethod
    def create_external_account(cls, acct, **kwargs):
        from edudream.modules.utils import log_request
        result = stripe.Account.create_external_account(
            account=acct,
            external_account={"account_number": kwargs.get("account_no"), "country": kwargs.get("country_code"),
                              "currency": kwargs.get("currency_code"), "routing_number": kwargs.get("routing_no"),
                              "object": "bank_account", }
        )
        log_request(f'Bank external account creation response: {result}')
        return result

    @classmethod
    def transfer_to_connect_account(cls, amount, acct, desc):
        from edudream.modules.utils import log_request
        result = stripe.Transfer.create(amount=int(amount * 100), currency="eur", destination=acct, description=desc)
        log_request(f'Transfer to connect account response: {result}')
        return result

    @classmethod
    def payout_to_external_account(cls, amount, acct, stripe_acct):
        from edudream.modules.utils import log_request
        result = stripe.Payout.create(
            amount=int(amount * 100), currency="eur", destination=acct, stripe_account=stripe_acct
        )
        log_request(f'Payout to external account response: {result}')
        return result

    @classmethod
    def get_account_balance(cls):
        from edudream.modules.utils import log_request
        result = stripe.Balance.retrieve()
        data = result.get("available")
        balance = 0
        eur_amount = [item['amount'] for item in data if item['currency'] == 'eur']
        if eur_amount:
            balance = eur_amount[0]
        log_request(f'Check balance response: {result}')
        return balance

    @classmethod
    def get_connect_account_balance(cls, acct):
        from edudream.modules.utils import log_request
        result = stripe.Balance.retrieve(expand=["instant_available.net_available"], stripe_account=acct)
        log_request(f'Check connect account balance response: {result}')
        return result




