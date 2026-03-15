import qrbill
from qrbill.bill import QRBill
from stdnum.iban import calc_check_digits
# Bank code 09000 (PostFinance) - non-QR IBAN
base_iban = "CH0009000000000000000"
valid_iban = "CH" + calc_check_digits(base_iban) + base_iban[4:]

# Test non-QR IBAN without reference
try:
    qr_bill = QRBill(
        account=valid_iban,
        creditor={
            "name": "My Parking Garage",
            "line1": "Parking Street 1",
            "line2": "1000 City",
            "country": "CH"
        },
        debtor={
            "name": "John Doe",
            "line1": "Underground Parking",
            "line2": "Switzerland",
            "country": "CH"
        },
        amount="15.50",
        currency="CHF",
        additional_information="Invoice 1",
    )
    qr_bill.as_svg("test_invoice.svg")
    print(f"Success with regular IBAN: {valid_iban}")
except Exception as e:
    print("Error:", e)
