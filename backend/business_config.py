"""Public business / payment notice for mobile web & clients."""
import os


def get_business_info() -> dict:
    return {
        "monthlyPrice": int(os.getenv("BUSINESS_MONTHLY_PRICE", "12900")),
        "yearlyPrice": int(os.getenv("BUSINESS_YEARLY_PRICE", "129000")),
        "bankName": os.getenv("BUSINESS_BANK_NAME", "하나은행"),
        "accountNumber": os.getenv("BUSINESS_ACCOUNT_NUMBER", "365-910996-44807"),
        "accountHolder": os.getenv("BUSINESS_ACCOUNT_HOLDER", "신일"),
        "contact": os.getenv("BUSINESS_CONTACT", "010-7237-1258"),
        "contactMethod": os.getenv("BUSINESS_CONTACT_METHOD", "카톡/문자"),
        "keyDeliveryMinutes": int(os.getenv("BUSINESS_KEY_DELIVERY_MINUTES", "10")),
    }
