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
    
    # @classmethod
    # def stripe_prebuilt_checkout(cls, payment_name, amount, **kwargs):
    #     success_url = kwargs.get("success_url")
    #     cancel_url = kwargs.get("cancel_url")
    #     mode = kwargs.get("mode", "payment")
    #     currency = kwargs.get("currency", "eur")
    #     client_reference_id = kwargs.get("client_reference_id")
    #     customer = kwargs.get("customer")
    #     customer_email = kwargs.get("customer_email")
    #     description = kwargs.get("description")
    #     tax_code = kwargs.get("tax_code")
    #
    #     images = kwargs.get("images", [])
    #     if type(images) is not list:
    #         return False, create_error_message('images', "images type must be list of images")
    #
    #     metadata = kwargs.get("metadata", {})
    #     if type(metadata) is not dict:
    #         return False, create_error_message('metadata', "metadata must be a dictionary")
    #
    #     recurring = kwargs.get("recurring", {})
    #     if recurring:
    #         if type(recurring) is not dict:
    #             return False, create_error_message('recurring', "recurring must be a dictionary")
    #         if not recurring.get('interval'):
    #             return False, create_error_message('recurring', "interval is required for a recurring payment")
    #         recurring_interval = ['day', 'week', 'month', 'year']
    #         if recurring.get('interval') not in recurring_interval:
    #             return False, create_error_message('recurring', f"interval must be one of {recurring_interval}")
    #         if recurring.get('interval_count'):
    #             interval = recurring.get('interval')
    #             interval_count = recurring.get('interval_count')
    #             if type(interval_count) is not int:
    #                 return False, create_error_message('recurring', f"interval_count must be an integer")
    #             if interval == 'day' and interval_count > 365:
    #                 return False, create_error_message('recurring', f"maximum of 365 days is allowed for interval count")
    #             if interval == 'week' and interval_count > 52:
    #                 return False, create_error_message('recurring', f"maximum of 52 weeks is allowed for interval count")
    #             if interval == 'month' and interval_count > 12:
    #                 return False, create_error_message('recurring', f"maximum of 12 months is allowed for interval count")
    #             if interval == 'year' and interval_count > 1:
    #                 return False, create_error_message('recurring', f"maximum of 1 year is allowed for interval count")
    #
    #     try:
    #         session = stripe.checkout.Session.create(
    #             line_items=[
    #                 {
    #                     'price_data': {
    #                         'currency': currency,
    #                         'product_data': {
    #                             'name': payment_name,
    #                             'description': description,
    #                             'images': images,
    #                             'metadata': metadata,
    #                             'tax_code': tax_code,
    #                         },
    #                         'unit_amount_decimal': float(amount) * 100,
    #                         'recurring': recurring,
    #                     },
    #                     'quantity': 1,
    #                 },
    #             ],
    #             mode=mode,
    #             success_url=success_url,
    #             cancel_url=cancel_url,
    #             client_reference_id=client_reference_id,
    #             customer=customer,
    #             customer_email=customer_email,
    #             metadata=metadata,
    #         )
    #         log.info(session)
    #         return True, session
    #     except Exception as ex:
    #         return False, create_error_message('source', f"{ex}")

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
    def create_connect_account(cls, user):
        from edudream.modules.utils import log_request
        account_token = stripe.Token.create(
            account={
                "individual": {"first_name": str(user.first_name), "last_name": str(user.last_name),
                                    "email": str(user.email)}, "tos_shown_and_accepted": True, "business_type": "individual"}, api_key=pk_key
        )
        log_request(f'Account creation token response: {account_token}')

        result = stripe.Account.create(
            type="custom", country=str(user.profile.country.alpha2code).upper(), email=str(user.email),
            capabilities={"card_payments": {"requested": True}, "transfers": {"requested": True}, },
            account_token=account_token.get("id"),

        )
        log_request(f'Connect account creation response: {result}')
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
    def payout_to_external_account(cls, amount, acct):
        from edudream.modules.utils import log_request
        result = stripe.Payout.create(amount=int(amount * 100), currency="eur", destination=acct)
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



