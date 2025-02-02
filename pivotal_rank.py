from typing import Dict, List


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
    print(f"Product match score: {match_score} ({mentioned_products}/{total_products})")
    return match_score


def get_stage_weight(stage_name: int) -> float:
    """Get weight based on opportunity stage"""
    stage_weights = {
        0: 1.0,
        1: 0.1,
        2: 0.3,
        3: 0.4, 
        4: 0.1
    }
    return stage_weights.get(stage_name, 0.0)


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
    print(f"Stage name: {opportunity.get('StageName', 'Unknown')}")
    print(f"Products count: {len(opportunity_products)}")
    print(f"Owner ID: {opportunity.get('OwnerId', 'Unknown')}")
    
    # Calculate individual components
    stage_weight = get_stage_weight(opportunity.get('StageName', ''))
    owner_match = calculate_owner_match(opportunity.get('OwnerId'), user_ids)
    
    # Log individual scores
    print(f"Stage weight: {stage_weight}")
    print(f"Owner match: {owner_match}")
    
    if opportunity_products:  # If we have products to match
        product_match = calculate_product_match(opportunity_products, transcript)
        print(f"Product match: {product_match}")
        
        # Calculate final score with all weights
        final_score = (
            (0.5 * product_match) +
            (0.4 * stage_weight) +
            (0.1 * owner_match)
        )
    else:  # If no products to match, redistribute weights
        print("No products to match, using stage and owner weights only")
        final_score = (
            (0.8 * stage_weight) +
            (0.2 * owner_match)
        )
    
    # Log final score
    print(f"Final score before normalization: {final_score}")
    
    # Normalize to ensure we don't exceed 1.0
    normalized_score = min(max(final_score, 0.0), 1.0)
    print(f"Final normalized score: {normalized_score}")
    
    return normalized_score
