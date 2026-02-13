"""
Legacy Payment Processor - Old credit card handling code
This file contains test credit card data and should be BLOCKED by the scanner
"""


class PaymentProcessor:
    def __init__(self):
        # Test credit card data - SECURITY VIOLATION
        self.test_card = "4532-1234-5678-9010"
        self.test_cvv = "123"
        self.test_expiry = "12/25"

    def validate_card_number(self, card_number):
        """Validate credit card using Luhn algorithm"""
        # Remove hyphens and spaces
        card_number = card_number.replace('-', '').replace(' ', '')

        # Check length
        if len(card_number) != 16:
            return False

        # Luhn algorithm
        total = 0
        reverse_digits = card_number[::-1]

        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n

        return total % 10 == 0

    def process_payment(self, card_number, cvv, expiry, amount):
        """Process a payment transaction - legacy synchronous method"""
        # Validate card
        if not self.validate_card_number(card_number):
            return {'success': False, 'error': 'Invalid card number'}

        # In legacy code, we just print the card details (very insecure!)
        print(f"Processing payment of ${amount}")
        print(f"Card: {card_number}")
        print(f"CVV: {cvv}")
        print(f"Expiry: {expiry}")

        # Simulate payment processing
        return {
            'success': True,
            'transaction_id': 'TXN-12345',
            'amount': amount
        }

    def process_refund(self, transaction_id, amount):
        """Process a refund - legacy method"""
        print(f"Processing refund of ${amount} for transaction {transaction_id}")

        return {
            'success': True,
            'refund_id': 'REF-67890',
            'amount': amount
        }

    def get_test_card_data(self):
        """Return test card data - SHOULD NOT BE IN PRODUCTION CODE!"""
        return {
            'card_number': self.test_card,
            'cvv': self.test_cvv,
            'expiry': self.test_expiry
        }


class SubscriptionManager:
    def __init__(self):
        self.processor = PaymentProcessor()

    def create_subscription(self, customer_id, card_number, plan_id):
        """Create recurring subscription - legacy implementation"""
        # Store card info in plain text - VERY INSECURE!
        subscription_data = {
            'customer_id': customer_id,
            'card_number': card_number,  # Should never store raw card numbers!
            'plan_id': plan_id,
            'status': 'active'
        }

        print(f"Created subscription: {subscription_data}")
        return subscription_data

    def charge_subscription(self, subscription_data, amount):
        """Charge a subscription - uses stored card number"""
        return self.processor.process_payment(
            card_number=subscription_data['card_number'],
            cvv='000',  # CVV shouldn't be stored
            expiry='12/99',
            amount=amount
        )


# Example usage with test data
if __name__ == "__main__":
    processor = PaymentProcessor()

    # Using test card data
    test_data = processor.get_test_card_data()
    result = processor.process_payment(
        card_number=test_data['card_number'],
        cvv=test_data['cvv'],
        expiry=test_data['expiry'],
        amount=99.99
    )

    print(f"Payment result: {result}")
