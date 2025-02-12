import crm_services


config = {
    "username": "SU",
    "password": "updateISI",
    "url_domain": "https://app.crmagic.ai:8000/CRMinterface/xml"
}

acrm_service = crm_services.ACRMService(config)

opportunities = acrm_service.get_opportunities_by_account_id("4294967297")

print(opportunities)
