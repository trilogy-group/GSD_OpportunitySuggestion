import logging
import json
from typing import List, Dict

from langchain_service import Speeds, service as langchain_svc

logger = logging.getLogger(__name__)

def calculate_product_match(opportunity_products: List[Dict], transcript: str) -> float:
    """Calculate how many products from the opportunity are mentioned in the transcript"""
    if not opportunity_products:
        return 0.0
    
    mentioned_products = 0
    total_products = len(opportunity_products)
    
    # Convert transcript to lowercase once
    transcript_lower = transcript.lower()
    
    for product in opportunity_products:
        product_name = product.get('product_name', '').lower()
        if not product_name:
            continue
            
        # Split product name into words and check if any word is in transcript
        product_words = product_name.split()
        for word in product_words:
            if len(word) > 3 and word in transcript_lower:  # Only check words longer than 3 chars
                mentioned_products += 1
                break  # Count the product as mentioned if any of its words are found
    
    match_score = mentioned_products / total_products if total_products > 0 else 0.0
    logger.debug(f"Product match score: {match_score} ({mentioned_products}/{total_products})")
    return match_score

def get_stage_weight(stage_name: str) -> float:
    """Get weight based on opportunity stage"""
    stage_weights = {
        # High probability stages (1.0 - 0.8)
        'engaged': 1.0,
        'proposal': 0.9,
        'quote follow-up': 0.85,
        'finalizing': 0.8,
        
        # Medium-high probability stages (0.7 - 0.6)
        'outreach': 0.7,
        'introduction': 0.7,
        'business': 0.65,
        'connect': 0.65,
        'engage': 0.65,
        'pending': 0.7,  # Increased from 0.6 to 0.7
        
        # Medium probability stages (0.5 - 0.4)
        'activation': 0.5,
        'review': 0.5,
        'identify resolution': 0.45,
        'resolution attempt': 0.45,
        
        # Low-medium probability stages (0.3 - 0.2)
        'resolution success': 0.3,
        'co-term': 0.25,
        
        # Low probability stages (0.1 - 0.0)
        'resolution fail/futile': 0.1,
        "won't process": 0.05,
        'closed won': 0.1,
        'closed lost': 0.0,
        'none': 0.0
    }
    return stage_weights.get(stage_name.lower(), 0.5)

def calculate_name_match(opportunity_name: str, transcript: str) -> float:
    """Simple name matching - can be enhanced with more sophisticated NLP"""
    opportunity_words = set(opportunity_name.lower().split())
    transcript_words = set(transcript.lower().split())
    
    if not opportunity_words:
        return 0.0
    
    matching_words = opportunity_words.intersection(transcript_words)
    return len(matching_words) / len(opportunity_words)

def calculate_owner_match(opportunity_owner_id: str, user_ids: List[str]) -> float:
    """Calculate if the opportunity owner is in the list of user IDs"""
    if not opportunity_owner_id or not user_ids:
        return 0.0
    
    return 1.0 if opportunity_owner_id in user_ids else 0.0

def rank_opportunity_score(opportunity: Dict, opportunity_products: List[Dict], transcript: str, user_ids: List[str]) -> float:
    """
    Calculate opportunity score based on multiple factors:
    If product_ids are provided:
        - Product match (50%)
        - Stage weight (40%)
        - Owner match (10%)
    If no product_ids:
        - Stage weight (80%)
        - Owner match (20%)
    """
    # Add debug logging
    logger.debug(f"Stage name: {opportunity.get('StageName', 'Unknown')}")
    logger.debug(f"Products count: {len(opportunity_products)}")
    logger.debug(f"Owner ID: {opportunity.get('OwnerId', 'Unknown')}")
    
    # Calculate individual components
    stage_weight = get_stage_weight(opportunity.get('StageName', ''))
    owner_match = calculate_owner_match(opportunity.get('OwnerId'), user_ids)
    
    # Log individual scores
    logger.debug(f"Stage weight: {stage_weight}")
    logger.debug(f"Owner match: {owner_match}")
    
    if opportunity_products:  # If we have products to match
        product_match = calculate_product_match(opportunity_products, transcript)
        logger.debug(f"Product match: {product_match}")
        
        # Calculate final score with all weights
        final_score = (
            (0.5 * product_match) +
            (0.4 * stage_weight) +
            (0.1 * owner_match)
        )
    else:  # If no products to match, redistribute weights
        logger.debug("No products to match, using stage and owner weights only")
        final_score = (
            (0.8 * stage_weight) +
            (0.2 * owner_match)
        )
    
    # Log final score
    logger.debug(f"Final score before normalization: {final_score}")
    
    # Normalize to ensure we don't exceed 1.0
    normalized_score = min(max(final_score, 0.0), 1.0)
    logger.debug(f"Final normalized score: {normalized_score}")
    
    return normalized_score

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

def determine_suggestion(opportunities: List[Dict], min_score_threshold: float = 0.25, score_difference_threshold: float = 0.1) -> List[Dict]:
    """
    Determine which opportunity should be suggested based on dynamic thresholds.
    
    Args:
        opportunities: List of ranked opportunities
        min_score_threshold: Minimum score required to be considered (default 0.25)
        score_difference_threshold: Required difference from next best score (default 0.1)
    
    Returns:
        List of opportunities with suggested flag
    """
    if not opportunities:
        return opportunities
        
    # Sort opportunities by rank in descending order
    sorted_opps = sorted(opportunities, key=lambda x: x['rank'], reverse=True)
    
    # Get top two scores
    top_score = sorted_opps[0]['rank']
    second_score = sorted_opps[1]['rank'] if len(sorted_opps) > 1 else 0
    
    # Check if top score meets minimum threshold and has enough separation from second best
    score_difference = top_score - second_score
    should_suggest = (top_score >= min_score_threshold and 
                     score_difference >= score_difference_threshold)
    
    # Add suggested flag to all opportunities
    for opp in sorted_opps:
        opp['suggested'] = should_suggest and opp['rank'] == top_score
        
    return sorted_opps
