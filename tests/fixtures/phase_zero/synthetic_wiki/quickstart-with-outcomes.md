# Quickstart with stated outcomes (4 steps)
---
title: Sample onboarding
source: https://docs.example.com/onboarding
---

# Sample onboarding

## 1. Create account

**Actions**
1. POST /v1/accounts with country=US

**Expected outcome:** Response includes id starting with acct_.

## 2. Create link

**Actions**
1. POST /v1/account_links

**Expected outcome:** Response includes a single-use url.

## 3. Redirect user

**Actions**
1. Send the user to the url field.

**Expected outcome:** User completes hosted onboarding.

## 4. Confirm via webhook

**Actions**
1. Listen for account.updated.

**Expected outcome:** charges_enabled becomes true when ready.
