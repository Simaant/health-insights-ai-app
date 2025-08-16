from transformers import pipeline

health_agent = pipeline("text2text-generation", model="google/flan-t5-large")

def run_health_agent_hf(flagged_markers: dict, wearable: dict = None):
    prompt = "Given this lab and wearable data, give lifestyle recommendations:\n\n"
    prompt += f"Lab markers: {flagged_markers}\n"
    if wearable:
        prompt += f"Wearable data: {wearable}\n"
    prompt += "Respond in bullet points, in plain language."

    response = health_agent(prompt, max_length=512)
    return response[0]["generated_text"]