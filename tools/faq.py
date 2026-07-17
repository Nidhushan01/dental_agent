"""Dental FAQ knowledge base and retrieval."""

FAQ_DATABASE = {
    # Post-operative care
    "post-extraction": "After a tooth extraction, keep the area clean and avoid touching it. Use ice for the first 24 hours to reduce swelling. Rinse gently with warm salt water after 24 hours. Take over-the-counter pain relief if needed. Avoid straw use and smoking for at least 5 days.",
    "post-extraction-care": "After a tooth extraction, keep the area clean and avoid touching it. Use ice for the first 24 hours to reduce swelling. Rinse gently with warm salt water after 24 hours. Take over-the-counter pain relief if needed. Avoid straw use and smoking for at least 5 days.",
    "extraction-aftercare": "After a tooth extraction, keep the area clean and avoid touching it. Use ice for the first 24 hours to reduce swelling. Rinse gently with warm salt water after 24 hours. Take over-the-counter pain relief if needed. Avoid straw use and smoking for at least 5 days.",
    "after-cleaning": "After a professional cleaning, your teeth may be slightly sensitive for 24-48 hours. Avoid hot or cold foods/drinks during this time. Continue brushing gently and use fluoride mouthwash. If sensitivity persists, consult your dentist.",
    "after-filling": "After a filling, avoid chewing on the treated side for at least 2 hours until the filling hardens. You may experience mild sensitivity which typically subsides within a few days. If you have persistent pain or bite issues, contact us.",
    "post-op": "Please follow post-operative instructions provided after your procedure. Keep the area clean, take prescribed medications as directed, and avoid strenuous activities for at least 48 hours. Contact us if you experience unusual pain or complications.",
    
    # Hours and availability
    "hours": "We are open Monday to Friday, 9:00 AM to 5:00 PM, and Saturday 10:00 AM to 2:00 PM. We are closed on Sundays and public holidays.",
    "office-hours": "We are open Monday to Friday, 9:00 AM to 5:00 PM, and Saturday 10:00 AM to 2:00 PM. We are closed on Sundays and public holidays.",
    "open": "We are open Monday to Friday, 9:00 AM to 5:00 PM, and Saturday 10:00 AM to 2:00 PM. We are closed on Sundays and public holidays.",
    
    # Insurance and payments
    "insurance": "We accept most major dental insurance plans including Delta Dental, Cigna, United Healthcare, and Aetna. Please bring your insurance card to your appointment. We can file claims directly with most insurers.",
    "payment": "We accept cash, credit cards (Visa, Mastercard, American Express), and debit cards. Payment plans are available for large procedures. Please discuss financing options with our front desk staff.",
    "cost": "General consultation: $50. Professional cleaning: $100-150. Fillings: $150-300 per tooth. Root canal: $800-1500. Extraction: $200-500. Prices vary based on complexity. Contact us for a detailed estimate.",
    
    # General questions
    "root-canal": "A root canal treatment involves removing infected pulp from inside the tooth and filling the canal. This stops the infection and saves the tooth. The procedure typically requires 1-2 appointments. Mild discomfort is normal for a few days afterward.",
    "implant": "A dental implant is an artificial tooth root made of titanium. It takes 3-6 months to integrate with the bone, then a crown is attached on top. Implants are a long-lasting solution for missing teeth.",
    "braces": "Braces straighten teeth over 18-36 months. We offer traditional metal braces and clear options. Monthly adjustments are needed. Good oral hygiene during treatment is essential.",
}


def get_faq(topic: str) -> str:
    """Retrieve FAQ answer by topic keyword matching.
    
    Args:
        topic: Topic keyword (e.g., 'post-extraction', 'hours', 'insurance')
    
    Returns:
        str: Answer text or a default message if topic not found
    """
    # Normalize input
    query = topic.lower().strip()
    
    # Direct lookup
    if query in FAQ_DATABASE:
        return FAQ_DATABASE[query]
    
    # Keyword matching
    for key, answer in FAQ_DATABASE.items():
        if query in key or key in query:
            return answer
    
    # Fallback
    return "I'm sorry, I don't have information on that topic. Please contact our office at 0117894561 for assistance."

