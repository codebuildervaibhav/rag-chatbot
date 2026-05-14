import re
import random

def get_logic_based_response(message: str, history: list[dict] = None) -> str:
    """
    A predefined logic-based response system that serves as a final fallback
    if both LLM APIs (Ollama and OpenAI) are unavailable.
    
    It generates contextual responses based on the latest user message.
    """
    msg_lower = message.lower().strip()
    
    # 1. Greetings
    if re.search(r'\b(hi|hello|hey|greetings|howdy)\b', msg_lower):
        return "Hello! I am currently running on my predefined logic fallback system since my AI engines are resting. How can I help you in this limited mode?"
        
    # 2. Farewells
    if re.search(r'\b(bye|goodbye|cya|see ya|later)\b', msg_lower):
        return "Goodbye! Hopefully, my full AI capabilities will be back online next time we chat."
        
    # 3. Help/Support
    if re.search(r'\b(help|support|assist)\b', msg_lower):
        return "You've caught me in offline mode, so my capabilities are limited. I can respond to basic queries conceptually, but complex answers will need my LLM brains!"
        
    # 4. Identity questions
    if re.search(r'\b(who are you|your name|who made you)\b', msg_lower):
        return "I am Casper, built by Vaibhav Singh Rana! Right now I'm operating in logic-based fallback mode."
        
    # 5. Question mark detection
    if msg_lower.endswith("?"):
        return f"That's a great question regarding '{message}'. Sadly, without my main LLM processors, I can't provide a detailed answer right now."
        
    # 6. Gratitude
    if re.search(r'\b(thanks|thank you|appreciate)\b', msg_lower):
        return "You're very welcome! (Sent from logic-based fallback)"
        
    # 7. Contextual history-based response
    if history and len(history) > 0:
        last_role = history[-1].get("role")
        if last_role == "assistant":
            return f"I hear you saying '{message}'. I'm currently just a logic-based fallback, so I'm doing my best to keep the conversation going!"

    # Default fallback using the message context
    responses = [
        f"I received your message: '{message}'. Note that my AI brains are fully offline at the moment.",
        f"Interesting point about '{message}'. Unfortunately, I'm stuck in logic-based fallback mode right now.",
        f"I'm operating on a predefined logic system currently. I understood your input as: '{message}'."
    ]
    
    return random.choice(responses)
