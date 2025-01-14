
import logging
import json

from langchain_service import Speeds, service as langchain_svc


logger = logging.getLogger(__name__)


def rank_opportunity_score(user_products: list,  transcript: str) -> dict:
    context = f"You are a senior software engineer. Given the following opportunity, rank it based on the products that are being discussed here: {transcript}."
    prompt = f"""
        These are the products that the sales representative is selling:
        {user_products}

        Return a double score between 0 and 1. Being closer to 1 means the opportunity is more likely to be the one being discussed.
        The response should be a double, not an integer, json, string, markdown or any other format.
        
        If the opportunity is not related to the products being discussed, set the score to 0.
    """
    
    rank = langchain_svc.chat(
            [{ 'role': 'user', 'content': context }],
            prompt,
            Speeds.FAST
        )
    
    return rank


def rank_opportunity(opportunity: dict, user_products: list, transcript: str) -> dict:
    context = f"You are a senior software engineer. Given the following opportunity, rank it based on the products that are being discussed here: {transcript}."
    prompt = f"""
        These are the products that the sales representative is selling:
        {user_products}

        Return the augmented opportunity with a score between 0 and 1. Being closer to 1 means the opportunity is more likely to be the one being discussed.
        The response should be a JSON object, not a string or markdown, with the following structure:
        
        {{
            "id": "The opportunity id",
            "name": "The opportunity name",
            "score": "The score of the opportunity"
        }}
        
        If the opportunity is not related to the products being discussed, set the score to 0.
        
        These files come from the Salesforce API:
        {opportunity}
    """
    
    ranked_opportunities = langchain_svc.chat(
            [{ 'role': 'user', 'content': context }],
            prompt,
            Speeds.FAST
        )
    
    logger.debug(f"Ranked opportunity: {ranked_opportunities}")
    
    json_ranked_opportunity = json.loads(ranked_opportunities)
    logger.debug(f"JSON Ranked opportunity: {json_ranked_opportunity}")
    
    return json_ranked_opportunity
