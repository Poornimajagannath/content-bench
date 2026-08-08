---
title: Create payment
source: https://docs.example.com/payments/create
---

# Create payment

**Method:** `POST`
**Path:** `/pts/v2/payments`

### Body fields

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| clientReferenceInformation.code | string | yes | Merchant reference |
| orderInformation.amountDetails.totalAmount | string | yes | Total |
| orderInformation.amountDetails.currency | string | yes | ISO 4217 |
