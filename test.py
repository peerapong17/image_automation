def process_complex_keywords(keywords_string):
    """Process keywords with complex rules for n-grams and prepositions."""
    prepositions = {
        'about', 'above', 'across', 'after', 'against', 'along', 'among', 
        'around', 'as', 'at', 'before', 'behind', 'below', 'beneath', 
        'beside', 'between', 'beyond', 'but', 'by', 'concerning', 'despite',
        'down', 'during', 'except', 'excluding', 'following', 'for', 'from',
        'in', 'inside', 'into', 'like', 'near', 'of', 'off', 'on', 'onto',
        'opposite', 'out', 'outside', 'over', 'past', 'per', 'regarding',
        'round', 'save', 'since', 'than', 'through', 'throughout', 'till',
        'to', 'toward', 'towards', 'under', 'underneath', 'unlike', 'until',
        'up', 'upon', 'via', 'with', 'within', 'without'
    }
    
    # Split into individual keywords
    keywords = [k.strip().lower() for k in keywords_string.split(',')]
    
    # Separate into simple and complex keywords
    simple_keywords = set()
    complex_keywords = []
    
    for kw in keywords:
        words = kw.split()
        if len(words) <= 2:
            simple_keywords.add(kw)
        else:
            complex_keywords.append(words)
    
    # Process complex keywords
    additional_keywords = []
    for complex_kw in complex_keywords:
        valid_subwords = []
        for word in complex_kw:
            if word not in prepositions and word not in simple_keywords:
                valid_subwords.append(word)
        if valid_subwords:
            additional_keywords.append(' '.join(complex_kw))
    
    # Combine all keywords
    final_keywords = list(simple_keywords) + additional_keywords
    return ', '.join(final_keywords)

# Test example
test_keywords = ("carved bone, bone carving, etched bone, tribal art, hand holding bone, "
                "object with etched patterns, artifact, ancient artifact, cultural artifact, "
                "ceremonial object, ritual object, hand, dark skin, close-up, detail, "
                "intricate carving, bone art, traditional art, indigenous art, ethnic art, "
                "handcraft, handmade, craft, carving, pattern, design, texture, geometric pattern, "
                "triangles, lines, ivory, bone, animal bone, object, holding, grip, display, "
                "history, culture, tradition, tribal, indigenous, ethnic, decorative art, "
                "ceremonial, ritual")

print("Processed keywords:", process_complex_keywords(test_keywords))