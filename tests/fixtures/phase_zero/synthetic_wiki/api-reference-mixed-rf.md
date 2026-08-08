Create Registration {#boarding-reg-create}
===============================

Endpoint {#boarding-reg-create-structural-api}
---------------------------------------------

**Production:** `POST https://api.cybersource.com/boarding/v1/registrations`

Required Fields {#boarding-reg-create-structural-api-rf}
--------------------------------------------------------

[organizationInformation.businessName](https://developer.cybersource.com/api-fields/boarding.html#organizationInformation-businessName)
:
Merchant legal name.

REST Example: Create Registration {#boarding-reg-create-structural-api-rest}
-----------------------------------------------------------------------------

Request

```
{"organizationInformation": {"businessName": "Acme"}}
```

Response

```
{"id": "reg_123", "status": "PENDING"}
```

Endpoint {#boarding-retrieve-orgs}
----------------------------------

**Test:** `GET https://apitest.cybersource.com/oms/v1/organizations`

REST Example: List Organizations {#boarding-retrieve-orgs-rest}
---------------------------------------------------------------

Request

```
GET /oms/v1/organizations
```

Response

```
{"organizations": []}
```
