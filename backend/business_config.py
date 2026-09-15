"""Public business / payment notice for mobile web & clients."""
import os


def get_business_info() -> dict:
    return {
        "monthlyPrice": int(os.getenv("BUSINESS_MONTHLY_PRICE", "24900")),
        "yearlyPrice": int(os.getenv("BUSINESS_YEARLY_PRICE", "249000")),
        "semiAnnualPrice": int(os.getenv("BUSINESS_SEMI_ANNUAL_PRICE", "124500")),
        "quarterlyPrice": int(os.getenv("BUSINESS_SEMI_ANNUAL_PRICE", "124500")),
        "legacyMonthlyPrice": int(os.getenv("BUSINESS_LEGACY_MONTHLY_PRICE", "12900")),
        "blogMonthlyPrice": int(os.getenv("BUSINESS_BLOG_MONTHLY_PRICE", "12900")),
        "blogSemiAnnualPrice": int(os.getenv("BUSINESS_BLOG_SEMI_ANNUAL_PRICE", "64500")),
        "blogYearlyPrice": int(os.getenv("BUSINESS_BLOG_YEARLY_PRICE", "129000")),
        "allinMonthlyPrice": int(os.getenv("BUSINESS_MONTHLY_PRICE", "24900")),
        "allinSemiAnnualPrice": int(os.getenv("BUSINESS_SEMI_ANNUAL_PRICE", "124500")),
        "allinYearlyPrice": int(os.getenv("BUSINESS_YEARLY_PRICE", "249000")),
        "bankName": os.getenv("BUSINESS_BANK_NAME", "하나은행"),
        "accountNumber": os.getenv("BUSINESS_ACCOUNT_NUMBER", "365-910996-44807"),
        "accountHolder": os.getenv("BUSINESS_ACCOUNT_HOLDER", "신일"),
        "contact": os.getenv("BUSINESS_CONTACT", "070-8065-1258"),
        "contactMethod": os.getenv("BUSINESS_CONTACT_METHOD", "카톡/문자"),
        "keyDeliveryMinutes": int(os.getenv("BUSINESS_KEY_DELIVERY_MINUTES", "10")),
        "operatorName": os.getenv("BUSINESS_OPERATOR_NAME", "ACROSSTOOL"),
    }
